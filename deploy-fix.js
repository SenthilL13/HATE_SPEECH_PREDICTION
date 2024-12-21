const { execSync } = require('child_process');

function runCommand(command) {
  try {
    return execSync(command, { encoding: 'utf8' });
  } catch (error) {
    return `Error: ${error.message}`;
  }
}

console.log('Starting deployment fix process...');

// Install all required dependencies
console.log('\nInstalling Python dependencies:');
console.log(runCommand('pip install -r requirements.txt'));

// Create a new requirements.txt with all necessary dependencies
const requirements = `
Flask==2.0.1
gunicorn==20.0.4
numpy>=1.22.0
opencv-python==4.5.3.56
Pillow==8.3.2
pytesseract==0.3.3
Flask-RESTful==0.3.8
flask-mysqldb==1.0.1
flask-migrate==3.0.1
bcrypt==3.2.0
Werkzeug==2.0.3
flask-cors==3.0.10
scikit-learn==0.24.2
pandas==1.3.5
flask-wtf==0.15.1
flask-login==0.5.0
flask-sqlalchemy==2.5.1
Flask-Bcrypt==1.0.1
`;

// Write the new requirements.txt
console.log('\nUpdating requirements.txt:');
require('fs').writeFileSync('requirements.txt', requirements.trim());
console.log('Requirements file updated.');

// Create a render.yaml configuration file
const renderConfig = `
services:
  - type: web
    name: hate-speech-prediction
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.11
      - key: FLASK_ENV
        value: production
`;

// Write the render.yaml file
console.log('\nCreating render.yaml configuration:');
require('fs').writeFileSync('render.yaml', renderConfig.trim());
console.log('Render configuration file created.');

console.log('\nDeployment fix complete. Please commit these changes and redeploy your application.');
console.log('\nImportant next steps:');
console.log('1. Commit the updated requirements.txt and new render.yaml files');
console.log('2. Push the changes to your repository');
console.log('3. Redeploy your application on Render');