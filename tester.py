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
    def __init__(self, api_key=None, custom_prompts=None):
        self.api_key = api_key or API_KEY
        if GraphonClient:
            self.client = GraphonClient(api_key=self.api_key)
        else:
            self.client = None
            
        if custom_prompts:
            self.prompts = custom_prompts
        else:
            self.prompts = [
            "Identify the primary target audience for this video based on visuals.",
            "List specific product categories that would be suitable for advertising here.",
            "Are there any brand safety concerns (violence, adult content, etc.)?",
            "What is the overall mood and which ad tone would match it?",
            "Identify any visible brands or logos in the video.",
            "Does the video content appeal to luxury or budget-conscious consumers?",
            "Is this content suitable for children and family-friendly ads?",
            "What specific hobbies or interests does the video cater to?",
            "Are there any celebrities or influencers present? If so, who?",
            "Describe the setting (indoor/outdoor, city/nature) for location-based targeting.",
            "Is the video pacing energetic/sports-oriented or calm/relaxing?",
            "What consumer problems or needs are implied in the content?",
            "List 5 objects in the video that could be shoppable items.",
            "Estimate the age range and gender of the people shown.",
            "Is there any text or overlay that keywords can be extracted from?",
            "What season or time of day is depicted for seasonal ad targeting?",
            "Does the video suggest a specific lifestyle (e.g., fitness, gaming, travel)?",
            "Rate the video's potential for driving e-commerce clicks (High/Medium/Low).",
            "Suggest 5 contextual ad keywords for this video.",
            "Identify the main activity happening and its relevance to services."
        ]

    async def process_video(self, file_path):
        if not self.client:
            raise RuntimeError("GraphonClient not initialized.")
            
        group_name = f"test_group_{int(time.time())}"
        print(f"Uploading {file_path} and creating group {group_name}...")
        
        self.group_id = await getattr(self.client, 'upload_process_and_create_group')( (
            file_paths=[file_path], 
            group_name=group_name
        )
        print(f"Group created. ID: {self.group_id}. Processing complete.")
        return self.group_id

    async def run_single_query(self, prompt, prompt_id=0):
        if not hasattr(self, 'group_id') or not self.group_id:
            raise RuntimeError("Group ID not set. Video must be processed first.")
            
        start_time = time.time()
        response = await self.client.query_group(group_id=self.group_id, query=prompt)
        end_time = time.time()
        latency = end_time - start_time
        
        response_text = getattr(response, 'answer', str(response))
        
        return {
            "prompt_id": prompt_id,
            "prompt": prompt,
            "response": response_text,
            "latency_sec": round(latency, 2),
            "response_len": len(response_text),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    async def run_test(self, file_path):
        try:
            if not getattr(self, 'group_id', None):
                await self.process_video(file_path)
                
            print("Starting Prompt Test...")
            for i, prompt in enumerate(self.prompts):
                result = await self.run_single_query(prompt, i)
                print(f"Finished prompt {i+1}/{len(self.prompts)}: {result['latency_sec']:.2f}s")
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
