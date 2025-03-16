# Database Integration Guide

This document provides guidance for integrating the Foundation Plan Analyzer with PostgreSQL or Supabase databases.

## Overview

The Foundation Plan Analyzer generates structured data about foundation plans, including:
- Corner coordinates
- Wall segments with measurements
- ICF metrics (total linear feet, corners, wall area, etc.)
- Wall thickness

This data can be stored in a relational database to enable:
- Searching and filtering foundation plans
- Comparing metrics across multiple plans
- Generating reports and visualizations
- Integrating with other systems

## Database Schema

### Recommended Table Structure

#### 1. analyses

This table stores the core information about each analysis run.

```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    drawing_name TEXT,
    project_id UUID,
    user_id UUID,
    wall_thickness TEXT,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. icf_metrics

This table stores the ICF-specific metrics calculated for each analysis.

```sql
CREATE TABLE icf_metrics (
    id SERIAL PRIMARY KEY,
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    total_linear_feet NUMERIC(10, 2),
    total_corners INTEGER,
    wall_area_sqft NUMERIC(10, 2),
    wall_thickness_feet NUMERIC(10, 2),
    concrete_volume_cuyd NUMERIC(10, 2),
    bounding_box_width_feet NUMERIC(10, 2),
    bounding_box_length_feet NUMERIC(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. corners

This table stores the corner coordinates for each analysis.

```sql
CREATE TABLE corners (
    id SERIAL PRIMARY KEY,
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    corner_id INTEGER NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(analysis_id, corner_id)
);
```

#### 4. walls

This table stores the wall segments for each analysis.

```sql
CREATE TABLE walls (
    id SERIAL PRIMARY KEY,
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    wall_id INTEGER NOT NULL,
    start_corner_id INTEGER NOT NULL,
    end_corner_id INTEGER NOT NULL,
    start_x INTEGER NOT NULL,
    start_y INTEGER NOT NULL,
    end_x INTEGER NOT NULL,
    end_y INTEGER NOT NULL,
    length_pixels NUMERIC(10, 2),
    length TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(analysis_id, wall_id)
);
```

#### 5. projects (Optional)

This table can be used to organize analyses into projects.

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    client_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

To optimize query performance, consider adding the following indexes:

```sql
-- For filtering analyses by project
CREATE INDEX idx_analyses_project_id ON analyses(project_id);

-- For filtering analyses by user
CREATE INDEX idx_analyses_user_id ON analyses(user_id);

-- For filtering metrics by analysis
CREATE INDEX idx_icf_metrics_analysis_id ON icf_metrics(analysis_id);

-- For filtering corners by analysis
CREATE INDEX idx_corners_analysis_id ON corners(analysis_id);

-- For filtering walls by analysis
CREATE INDEX idx_walls_analysis_id ON walls(analysis_id);
```

## Integration with PostgreSQL

### Connection Setup

```python
import psycopg2
import psycopg2.extras

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="foundation_analyzer",
    user="postgres",
    password="your_password"
)

# Enable UUID type
psycopg2.extras.register_uuid()

# Create a cursor
cur = conn.cursor()
```

### Inserting Data

```python
from src.database_utils import prepare_for_database, generate_postgresql_statements

# Load analysis data
with open("outputs/perimeter_walls.json", "r") as f:
    data = json.load(f)

# Prepare data for database
db_ready_data = prepare_for_database(
    data, 
    drawing_name="foundation_plan_1",
    project_id="550e8400-e29b-41d4-a716-446655440000"
)

# Generate SQL statements
sql_statements = generate_postgresql_statements(db_ready_data)

# Execute SQL statements
for table, sql in sql_statements.items():
    cur.execute(sql)

# Commit the transaction
conn.commit()
```

### Sample Queries

#### Get all analyses for a project

```sql
SELECT a.id, a.drawing_name, a.timestamp, m.total_linear_feet, m.concrete_volume_cuyd
FROM analyses a
LEFT JOIN icf_metrics m ON a.id = m.analysis_id
WHERE a.project_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY a.timestamp DESC;
```

#### Get detailed wall information for an analysis

```sql
SELECT w.wall_id, w.length, 
       c1.x AS start_x, c1.y AS start_y,
       c2.x AS end_x, c2.y AS end_y
FROM walls w
JOIN corners c1 ON w.analysis_id = c1.analysis_id AND w.start_corner_id = c1.corner_id
JOIN corners c2 ON w.analysis_id = c2.analysis_id AND w.end_corner_id = c2.corner_id
WHERE w.analysis_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY w.wall_id;
```

#### Compare metrics across multiple analyses

```sql
SELECT a.drawing_name, 
       m.total_linear_feet, 
       m.total_corners,
       m.concrete_volume_cuyd
FROM analyses a
JOIN icf_metrics m ON a.id = m.analysis_id
WHERE a.project_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY m.total_linear_feet DESC;
```

## Integration with Supabase

### Connection Setup

```javascript
// JavaScript example using Supabase client
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://your-project.supabase.co'
const supabaseKey = 'your-supabase-key'
const supabase = createClient(supabaseUrl, supabaseKey)
```

```python
# Python example using Supabase client
from supabase import create_client

supabase_url = "https://your-project.supabase.co"
supabase_key = "your-supabase-key"
supabase = create_client(supabase_url, supabase_key)
```

### Inserting Data

```python
from src.database_utils import prepare_for_database, generate_supabase_payload

# Load analysis data
with open("outputs/perimeter_walls.json", "r") as f:
    data = json.load(f)

# Prepare data for database
db_ready_data = prepare_for_database(
    data, 
    drawing_name="foundation_plan_1",
    project_id="550e8400-e29b-41d4-a716-446655440000"
)

# Generate Supabase payload
payload = generate_supabase_payload(db_ready_data)

# Insert data into Supabase tables
for table, records in payload.items():
    if records:
        response = supabase.table(table).insert(records).execute()
        # Check response for errors
```

### Row-Level Security (RLS) Policies

For Supabase, consider implementing the following RLS policies:

#### analyses table

```sql
-- Allow users to select their own analyses
CREATE POLICY "Users can view their own analyses"
ON analyses FOR SELECT
USING (auth.uid() = user_id);

-- Allow users to insert their own analyses
CREATE POLICY "Users can insert their own analyses"
ON analyses FOR INSERT
WITH CHECK (auth.uid() = user_id);
```

#### Related tables (icf_metrics, corners, walls)

```sql
-- Allow users to select data related to their analyses
CREATE POLICY "Users can view their own metrics"
ON icf_metrics FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM analyses
        WHERE analyses.id = icf_metrics.analysis_id
        AND analyses.user_id = auth.uid()
    )
);
```

Apply similar policies to the corners and walls tables.

## Batch Processing

For processing multiple foundation plans in batch:

```python
from src.database_utils import batch_process_results
import glob

# Get all JSON result files
result_files = glob.glob("outputs/*.json")

# Process all files
summary = batch_process_results(
    result_files,
    output_dir="outputs/database",
    project_id="550e8400-e29b-41d4-a716-446655440000"
)

print(f"Processed {summary['total_processed']} files")
print(f"Failed to process {summary['total_failed']} files")
```

## Best Practices

1. **Use Transactions**: When inserting related data across multiple tables, use database transactions to ensure data consistency.

2. **Implement Error Handling**: Add robust error handling for database operations, especially for batch processing.

3. **Consider Data Versioning**: If foundation plans may be reanalyzed, implement a versioning strategy to track changes over time.

4. **Add Indexes for Common Queries**: Monitor query performance and add indexes for frequently used query patterns.

5. **Implement Backup Strategy**: Regularly backup your database, especially before batch operations.

6. **Use Parameterized Queries**: When building custom queries, always use parameterized queries to prevent SQL injection.

7. **Consider Data Archiving**: Implement a strategy for archiving old or unused analyses to maintain database performance.

## Environment Variables for Database Integration

This project uses environment variables for database credentials and configuration. You can add these to your `.env` file:

```
# PostgreSQL connection parameters
POSTGRES_HOST=localhost
POSTGRES_DB=foundation_analyzer
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Supabase connection parameters
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

## Example Integration Workflow

1. Set up environment variables for API keys and database credentials
2. Analyze a foundation plan using the perimeter wall extractor
3. Prepare the output data for database storage
4. Insert the data into the database
5. Query the database to retrieve and compare results

```python
import os
import json
import subprocess
from src.database_utils import prepare_for_database, generate_postgresql_statements

# 1. Analyze foundation plan
image_path = "src/Screenshot.png"
cmd = [
    "python", 
    "src/perimeter_wall_extractor.py", 
    image_path, 
    "--use_llm",
    "--no_visualize"
]
subprocess.run(cmd)

# 2. Prepare data for database
with open("outputs/perimeter_walls.json", "r") as f:
    data = json.load(f)

db_ready_data = prepare_for_database(
    data, 
    drawing_name=os.path.basename(image_path),
    project_id="550e8400-e29b-41d4-a716-446655440000"
)

# 3. Generate and execute SQL statements
sql_statements = generate_postgresql_statements(db_ready_data)

# (Execute SQL statements using your database connection)

# 4. Save database-ready JSON for reference
with open("outputs/database_ready.json", "w") as f:
    json.dump(db_ready_data, f, indent=2)
