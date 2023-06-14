import subprocess
import os

def check_gcloud_installation():
    try:
        result = subprocess.run(['gcloud', 'version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("gcloud command not found. Please install Google Cloud SDK.")
            return False
        else:
            print(result.stdout.decode('utf-8'))
            return True
    except Exception as e:
        print("An error occurred:", e)
        return False

def check_gcloud_configuration():
    try:
        result = subprocess.run(['gcloud', 'config', 'list', 'account', '--format', 'value(core.account)'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0 or result.stdout.decode('utf-8').strip() == "":
            print("gcloud is not configured with a cloud account.")
            return False
        else:
            print("gcloud is configured with the account:", result.stdout.decode('utf-8'))
            return True
    except Exception as e:
        print("An error occurred:", e)
        return False

def create_bucket(bucket_name):
    try:
        result = subprocess.run(['gsutil', 'mb', f'gs://{bucket_name}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("Failed to create bucket. Error:", result.stderr.decode('utf-8'))
            return False
        else:
            print("Bucket created successfully.")
            return True
    except Exception as e:
        print("An error occurred:", e)
        return False

def create_function_files(bucket_name):
    index_js_content = f"""
    const {{Storage}} = require('@google-cloud/storage');
    const storage = new Storage();

    exports.{bucket_name} = async (req, res) => {{
        const data = req.body;
        const filename = `webhook-${{Date.now()}}.json`;
        const bucketName = '{bucket_name}';

        const file = storage.bucket(bucketName).file(filename);
        await file.save(JSON.stringify(data));

        res.status(200).send(`Successfully wrote ${{filename}} to bucket ${{bucketName}}`);
    }};
    """
    
    package_json_content = f"""
    {{
        "name": "{bucket_name}",
        "version": "1.0.0",
        "description": "A cloud function to write webhooks to GCS",
        "main": "index.js",
        "dependencies": {{
            "@google-cloud/storage": "^5.8.5"
        }}
    }}
    """

    os.makedirs("webhook-function", exist_ok=True)
    
    try:
        with open(f"webhook-function/index.js", "w") as f:
            f.write(index_js_content)
        print("index.js file created successfully.")
    except Exception as e:
        print("An error occurred while creating index.js:", e)
        return False

    try:
        with open(f"webhook-function/package.json", "w") as f:
            f.write(package_json_content)
        print("package.json file created successfully.")
    except Exception as e:
        print("An error occurred while creating package.json:", e)
        return False

    return True

def deploy_function(bucket_name):
    try:
        result = subprocess.run(['gcloud', 'functions', 'deploy', bucket_name, '--runtime', 'nodejs14', '--trigger-http', '--allow-unauthenticated', '--source', './webhook-function'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("Failed to deploy function. Error:", result.stderr.decode('utf-8'))
            return False
        else:
            print("Function deployed successfully.")
            return True
    except Exception as e:
        print("An error occurred:", e)
        return False

def get_function_url(bucket_name):
    try:
        result = subprocess.run(['gcloud', 'functions', 'describe', bucket_name, '--format', 'value(httpsTrigger.url)'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("Failed to get function URL. Error:", result.stderr.decode('utf-8'))
            return None
        else:
            url = result.stdout.decode('utf-8').strip()
            print("Function URL:", url)
            return url
    except Exception as e:
        print("An error occurred:", e)
        return None

def main():
    if not check_gcloud_installation() or not check_gcloud_configuration():
        return

    bucket_name = input("Enter the bucket name: ")
    if not create_bucket(bucket_name):
        return

    if not create_function_files(bucket_name):
        return

    if not deploy_function(bucket_name):
        return

    get_function_url(bucket_name)

if __name__ == "__main__":
    main()

