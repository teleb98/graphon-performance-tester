import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
from tester import GraphonTester
import os

st.set_page_config(page_title="Graphon Performance Tester", layout="wide")

st.title("Graphon VLM Performance Dashboard")
st.markdown("Test latency and reasoning capabilities of Graphon VLM vs standard VLMs.")

# Sidebar - Configuration
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input("API Key", value="", type="password", help="Enter your Graphon API Key here")

uploaded_file = st.sidebar.file_uploader("Upload Video File", type=["mp4", "mov", "avi"])
youtube_url = st.sidebar.text_input("Or Enter YouTube URL")

# Session State for storing results
if "test_results" not in st.session_state:
    st.session_state.test_results = None

# Helper to download YouTube video
def download_youtube_video(url, output_path):
    import yt_dlp
    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        st.error(f"Failed to download YouTube video: {e}")
        return False

def download_direct_video(url, output_path):
    import requests
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        return True
    except Exception as e:
        st.error(f"Failed to download video from URL: {e}")
        return False

# Main execution block
if st.sidebar.button("Run Performance Test"):
    target_path = None
    is_temp = False
    
    if not api_key_input:
        st.error("Please enter a valid API Key in the sidebar.")
        st.stop()
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        target_path = f"temp_{uploaded_file.name}"
        with open(target_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        is_temp = True
        st.info(f"Using uploaded file: {uploaded_file.name}")
        
    elif youtube_url:
        st.info(f"Downloading video from: {youtube_url}...")
        # Clean URL to create a safe filename
        safe_name = "".join([c for c in youtube_url if c.isalnum() or c in ('-','_')])[-10:]
        target_path = f"temp_vid_{safe_name}.mp4"
        
        # Remove if exists from previous run
        if os.path.exists(target_path):
            os.remove(target_path)
            
        with st.spinner("Downloading video..."):
            # Check if it looks like a YouTube URL
            if "youtube.com" in youtube_url or "youtu.be" in youtube_url:
                success = download_youtube_video(youtube_url, target_path)
            else:
                # Try direct download
                success = download_direct_video(youtube_url, target_path)
                
            if success:
                st.success("Download complete.")
                is_temp = True
            else:
                st.error("Download failed. Please try a different URL, a direct MP4 link, or upload a file.")
                target_path = None
    
    else:
        # Fallback to local sample if available
        sample_path = "sample_video.mp4"
        if os.path.exists(sample_path):
            st.info(f"No input provided. Using local sample video: {sample_path}")
            target_path = sample_path
            is_temp = False # Don't delete the sample file
        else:
            st.warning("Please upload a file, enter a YouTube URL, or ensure 'sample_video.mp4' is in the directory.")

    if target_path:
        # Initialize Tester
        tester = GraphonTester(api_key=api_key_input)
        
        # Prepare UI placeholders for real-time updates
        st.divider()
        st.subheader("Real-time Analysis Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Metrics placeholders
        m_col1, m_col2, m_col3 = st.columns(3)
        metric_latency = m_col1.empty()
        metric_tokens = m_col2.empty()
        metric_count = m_col3.empty()
        
        # Charts placeholders
        chart_latency_spot = st.empty()
        chart_scatter_spot = st.empty()
        table_spot = st.empty()
        
        results_list = []
        
        async def run_streaming_test():
            idx = 0
            total_prompts = len(tester.prompts)
            
            async for result in tester.run_test(target_path):
                results_list.append(result)
                idx += 1
                
                # Update DataFrame
                df_current = pd.DataFrame(results_list)
                if 'Reasoning Depth' not in df_current.columns:
                     df_current['Reasoning Depth'] = ""
                
                # Update Metrics
                avg_lat = df_current['latency_sec'].mean()
                tot_len = df_current['response_len'].sum()
                
                metric_latency.metric("Avg Latency (s)", f"{avg_lat:.2f}")
                metric_tokens.metric("Total Length (chars)", f"{tot_len}")
                metric_count.metric("Prompts Completed", f"{idx}/{total_prompts}")
                
                # Update Progress
                progress_bar.progress(min(idx / total_prompts, 1.0))
                status_text.text(f"Processing: {result.get('prompt', 'Unknown')}")
                
                # Update Charts (every update might be too heavy? let's try)
                with chart_latency_spot:
                    fig_lat = px.bar(df_current, x='prompt', y='latency_sec', title="Live Latency", text='latency_sec')
                    fig_lat.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_lat, use_container_width=True, key=f"lat_{idx}")
                    
                with chart_scatter_spot:
                    fig_scat = px.scatter(df_current, x='response_len', y='latency_sec', size='response_len', 
                                          title="Live Latency vs Length")
                    st.plotly_chart(fig_scat, use_container_width=True, key=f"scat_{idx}")
                    
                # Update Table
                with table_spot:
                    st.dataframe(df_current[['prompt', 'response', 'latency_sec', 'response_len']], use_container_width=True)
            
            return pd.DataFrame(results_list)

        with st.spinner("Initializing Graphon Env & Indexing Video..."):
            try:
                final_df = asyncio.run(run_streaming_test())
                st.session_state.test_results = final_df
                st.success("Analysis Complete!")
            except Exception as e:
                st.error(f"Error during streaming: {e}")
            finally:
                if is_temp and os.path.exists(target_path):
                    os.remove(target_path)

# Final Review Section (Static view after run)
if st.session_state.test_results is not None:
    st.divider()
    st.header("Final Report")
    df = st.session_state.test_results
    
    st.download_button("Download Results CSV", df.to_csv().encode('utf-8'), "graphon_results.csv", "text/csv")
    
    st.subheader("VLM Comparison Notes")
    st.text_area("Notes", placeholder="Enter your observations here...", key="final_notes")

