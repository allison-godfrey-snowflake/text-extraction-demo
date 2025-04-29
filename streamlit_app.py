import streamlit as st
import os
import tempfile
from snowflake.snowpark.context import get_active_session

def get_files_in_stage(stage_path):
    # Use Streamlit's built-in Snowflake connection
    cursor = st.connection("snowflake").cursor()
    
    try:
        # Execute LIST command to get files in stage
        result = cursor.execute(f"LIST @{stage_path}")
        
        # Extract just the file names from the results
        # The file name is typically in the first position (index 0)
        file_names = [file_info[0].split('/')[-1] for file_info in result]
        
        return file_names
    except Exception as e:
        st.error(f"Error accessing stage: {e}")
        return []

def extract_text_from_image(stage_path, image_file):
    # Use Streamlit's built-in Snowflake connection
    conn = st.connection("snowflake")
    
    try:
        # Use Snowflake Cortex to extract text from image
        query = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet',
            'Please extract the text from this sample. If there are equations, please have them nicely formatted in LaTeX.',
            TO_FILE('@{stage_path}', '{image_file}'))
        """
        result = conn.query(query)
        
        # Extract the first value from the result
        if not result.empty:
            return result.iloc[0, 0]
        else:
            return "No text extracted"
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def main():
    st.title("Handwriting Text Extraction: Demo")
    
    # Input for stage path
    stage_path = 'demo_text_extraction.sample_images.image_files'
    
    if stage_path:
        image_files = get_files_in_stage(stage_path)
        
        if image_files:
            selected_image = st.selectbox("Select an image file", image_files, key="extract_image")
            
            session = get_active_session()

            image=session.file.get_stream(f"@demo_text_extraction.sample_images.image_files/{selected_image}" , decompress=False).read()

            st.image(image)
            
            if selected_image:
                file_ext = selected_image.split('.')[-1].lower() if '.' in selected_image else ''
                image_extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp']
                
                if file_ext in image_extensions or st.checkbox("Force extraction (if not an image file)"):
                    if st.button("Extract Text from Image"):
                        with st.spinner("Extracting text using Claude AI..."):
                            extracted_text = extract_text_from_image(stage_path, selected_image)
                            
                            # Display the extracted text
                            st.subheader("Extracted Text:")
                            st.markdown(extracted_text)
                            
                            # Option to copy text
                            st.text_area("Copy extracted text:", extracted_text, height=300)
                else:
                    st.warning(f"Selected file '{selected_image}' doesn't appear to be an image. Select a file with an image extension or check 'Force extraction'.")
        else:
            st.info("No files found in the specified stage or the stage doesn't exist.")

if __name__ == "__main__":
    main()
