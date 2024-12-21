const { execSync } = require('child_process');

function runCommand(command) {
  try {
    return execSync(command, { encoding: 'utf8' });
  } catch (error) {
    return `Error: ${error.message}`;
  }
}

console.log('Starting troubleshooting process...');

// Update system packages
console.log('Updating system packages:');
console.log(runCommand('sudo apt-get update && sudo apt-get upgrade -y'));

// Install system dependencies for numpy
console.log('\nInstalling system dependencies for numpy:');
console.log(runCommand('sudo apt-get install -y build-essential libatlas-base-dev'));

// Install Python development files
console.log('\nInstalling Python development files:');
console.log(runCommand('sudo apt-get install -y python3-dev'));

// Upgrade pip and setuptools
console.log('\nUpgrading pip and setuptools:');
console.log(runCommand('pip install --upgrade pip setuptools wheel'));

// Install numpy using a pre-built wheel
console.log('\nInstalling numpy using a pre-built wheel:');
console.log(runCommand('pip install numpy --only-binary=numpy'));

// Install gunicorn
console.log('\nInstalling gunicorn:');
console.log(runCommand('pip install gunicorn'));

// Verify gunicorn installation
console.log('\nVerifying gunicorn installation:');
console.log(runCommand('which gunicorn'));

console.log('\nTroubleshooting complete. Please review the output for any errors.');
