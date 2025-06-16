from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
import subprocess
import os
import tempfile
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="DOC to Text Converter")

# Create a thread pool for running blocking subprocess calls
executor = ThreadPoolExecutor()

async def run_catdoc(file_path: str) -> str:
    # Run blocking subprocess in a separate thread
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            executor,
            lambda: subprocess.run(
                ["catdoc", file_path],
                capture_output=True,
                text=True,
                check=True
            ).stdout
        )
        return result
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"catdoc failed: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/convert-doc/", response_class=PlainTextResponse)
async def convert_doc(file: UploadFile = File(...)):
    # Check if the file is a .doc file
    if not file.filename.lower().endswith('.doc'):
        raise HTTPException(status_code=400, detail="Only .doc files are supported")
    
    # Create a temporary directory to store the uploaded file
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, file.filename)
        
        # Save the uploaded file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
        # Check if catdoc is installed
        if shutil.which("catdoc") is None:
            raise HTTPException(status_code=500, detail="catdoc is not installed. Please install it using 'sudo apt install catdoc'")
        
        # Run catdoc in a non-blocking way
        return await run_catdoc(file_path)

@app.on_event("shutdown")
def shutdown_event():
    # Clean up the thread pool
    executor.shutdown()