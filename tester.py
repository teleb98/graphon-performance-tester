import asyncio
import time
import pandas as pd
import os
# Assuming the package is installed as 'graphon-client' but imported as 'graphon' or similar. 
# The user's blueprint used 'from graphon import GraphonClient'. 
# We will use that, but wrap it in try-except to hint user if it fails.
try:
    from graphon import GraphonClient
except ImportError:
    # Fallback or placeholder if the package name is different, usually it is 'graphon'
    try:
        from graphon_client import GraphonClient
    except ImportError:
        print("Warning: Could not import GraphonClient. Please check the package name.")
        GraphonClient = None

API_KEY = os.getenv("GRAPHON_API_KEY", "")

class GraphonTester:
    def __init__(self, api_key=None):
        self.api_key = api_key or API_KEY
        if GraphonClient:
            self.client = GraphonClient(api_key=self.api_key)
        else:
            self.client = None
            
        self.prompts = [
            "What is the main color scheme of this video?",
            "When does the singer's outfit change?",
            "List 5 key objects appearing in the video.",
            "Choose the mood of this video from 'Sad', 'Joyful', 'Angry' and explain why.",
            "Summarize the storyline of the music video.",
            "Describe the lighting in the opening scene.",
            "Are there any animals in the video? If so, what are they?",
            "What text appears on the screen, if any?",
            "Describe the camera movement in the first 10 seconds.",
            "How many distinct locations are shown?",
            "Is there a dance sequence? Describe it.",
            "What is the climax of the video?",
            "Describe the ending scene.",
            "What is the genre of this music video visual?",
            "Identify the gender and approximate age of the main character.",
            "Are there any special visual effects used?",
            "What emotions do the characters' facial expressions convey?",
            "Is the video fast-paced or slow-paced?",
            "Generate 5 keywords for tagging this video.",
            "Write a creative caption for a thumbnail of this video."
        ]

    async def run_test(self, file_path):
        if not self.client:
            raise RuntimeError("GraphonClient not initialized.")
            
        # 1. Upload & Process & Create Group
        # Create a unique group name
        group_name = f"test_group_{int(time.time())}"
        print(f"Uploading {file_path} and creating group {group_name}...")
        
        try:
            # Use upload_process_and_create_group which handles upload, processing and grouping
            # Note: file_paths expects a list
            group_id = await self.client.upload_process_and_create_group(
                file_paths=[file_path], 
                group_name=group_name
            )
            print(f"Group created. ID: {group_id}. Processing complete.")
            
            # 2. Query Loop
            print("Starting Prompt Test...")
            for i, prompt in enumerate(self.prompts):
                start_time = time.time()
                
                # Graphon API call - query_group
                # Correct signature: query_group(group_id, query, ...)
                response = await self.client.query_group(group_id=group_id, query=prompt)
                
                end_time = time.time()
                latency = end_time - start_time
                
                # Handle response structure
                # QueryResponse object has 'answer' attribute
                response_text = getattr(response, 'answer', str(response))
                
                result = {
                    "prompt_id": i,
                    "prompt": prompt,
                    "response": response_text,
                    "latency_sec": round(latency, 2),
                    "response_len": len(response_text),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                print(f"Finished prompt {i+1}/{len(self.prompts)}: {latency:.2f}s")
                yield result
                
        except Exception as e:
            print(f"Error during test: {e}")
            yield {
                "prompt": "ERROR",
                "response": str(e),
                "latency_sec": 0,
                "response_len": 0
            }

if __name__ == "__main__":
    # Test run
    tester = GraphonTester()
    # Replace with a valid file path for testing locally if needed
    async def main():
        try:
            async for result in tester.run_test("sample_video.mp4"):
                pass # The method already prints progress
        except Exception as e:
            print(f"Run Error: {e}")
            
    try:
        asyncio.run(main()) 
    except KeyboardInterrupt:
        print("Test stopped.")
    print("GraphonTester run complete.")
