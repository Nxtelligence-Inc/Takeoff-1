const { exec } = require('child_process');
const path = require('path');

// Sample image path
const sampleImagePath = path.join(__dirname, 'SampleDrawings', 'Screenshot.png');

// Output directory
const outputDir = path.join(__dirname, 'test_output');

// Build command
const pythonScript = path.join(__dirname, 'src', 'perimeter_wall_extractor.py');
const command = `python "${pythonScript}" "${sampleImagePath}" --overall_width "38'-0" --output_dir "${outputDir}"`;

console.log('Executing command:', command);

// Execute Python script
exec(command, (error, stdout, stderr) => {
  if (error) {
    console.error(`Execution error: ${error}`);
    return;
  }
  
  if (stderr) {
    console.error(`stderr: ${stderr}`);
  }
  
  console.log('Python script output:');
  console.log(stdout);
  
  console.log('Analysis completed successfully!');
});
