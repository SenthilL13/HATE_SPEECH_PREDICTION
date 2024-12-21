const { execSync } = require('child_process');

function runCommand(command) {
  try {
    return execSync(command, { encoding: 'utf8', stdio: 'inherit' });
  } catch (error) {
    console.error(`Error executing command: ${command}`);
    console.error(error.message);
    return null;
  }
}

console.log('Starting deployment troubleshooting...');

// Update pip and setuptools
console.log('\nUpdating pip and setuptools:');
runCommand('pip install --upgrade pip setuptools wheel');

// Install numpy using a pre-built wheel
console.log('\nInstalling numpy using a pre-built wheel:');
runCommand('pip install numpy --only-binary=numpy');

// Install other dependencies
console.log('\nInstalling other dependencies:');
runCommand('pip install -r requirements.txt');

// Verify gunicorn installation
console.log('\nVerifying gunicorn installation:');
runCommand('which gunicorn');
runCommand('gunicorn --version');

// Check Python version
console.log('\nChecking Python version:');
runCommand('python --version');

// Print current working directory and list files
console.log('\nCurrent working directory:');
runCommand('pwd');
console.log('\nListing files in current directory:');
runCommand('ls -la');

// Check if app.py exists
console.log('\nChecking for app.py:');
runCommand('ls app.py');

console.log('\nTroubleshooting complete. Please review the output for any errors.');