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

