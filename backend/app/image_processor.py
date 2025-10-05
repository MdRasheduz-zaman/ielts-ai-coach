import base64
import logging
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

# Initialize Gemini with vision capabilities
vision_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.3,
    max_retries=3
)

async def extract_image_description(image_base64: str) -> str:
    """
    Extract detailed description from uploaded image for IELTS Task 1.
    
    Args:
        image_base64: Base64 encoded image data
        
    Returns:
        Detailed description of the visual data
        
    Raises:
        Exception: If image processing fails
    """
    try:
        logger.info("Starting image analysis for Task 1")
        
        # Create the prompt for image analysis
        prompt = """
        You are an IELTS expert analyzing visual data for Task 1. Examine this image carefully and provide a comprehensive description that would help a student write their Task 1 response.

        Please describe:

        1. **Type of Visual**: What kind of chart/graph/table/diagram is this?
        2. **Title and Labels**: What is the title? What are the axis labels, categories, or sections?
        3. **Key Data Points**: What are the main figures, percentages, or values shown?
        4. **Time Period**: What time frame does the data cover?
        5. **Units of Measurement**: What units are used (%, millions, years, etc.)?
        6. **Main Trends**: What are the most significant patterns, changes, or comparisons?
        7. **Notable Features**: Any striking differences, peaks, or anomalies?

        Provide a detailed, factual description that captures all the essential information a student would need to write an accurate Task 1 response. Focus on objective data rather than analysis or interpretation.

        Format your response as clear, organized information that can be directly used for Task 1 writing.
        """

        # Create message with image
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                }
            ]
        )

        # Get response from Gemini Vision
        response = await vision_llm.ainvoke([message])
        
        description = response.content.strip()
        
        if not description:
            raise ValueError("No description generated from image")
        
        logger.info(f"Successfully extracted image description: {len(description)} characters")
        return description
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise Exception(f"Failed to analyze image: {str(e)}")

def validate_image_base64(image_data: str) -> bool:
    """
    Validate base64 image data.
    
    Args:
        image_data: Base64 encoded image string
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Try to decode the base64 data
        decoded = base64.b64decode(image_data)
        
        # Check if it's a reasonable size (not empty, not too large)
        if len(decoded) < 100:  # Too small
            return False
        if len(decoded) > 10 * 1024 * 1024:  # Larger than 10MB
            return False
            
        # Check for common image headers
        image_headers = [
            b'\xff\xd8\xff',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF87a',  # GIF87a
            b'GIF89a',  # GIF89a
            b'RIFF',  # WebP (starts with RIFF)
        ]
        
        for header in image_headers:
            if decoded.startswith(header):
                return True
                
        return False
        
    except Exception:
        return False

# Alternative function for extracting specific chart types
async def extract_chart_data(image_base64: str, chart_type_hint: Optional[str] = None) -> dict:
    """
    Extract structured data from charts/graphs for more detailed analysis.
    
    Args:
        image_base64: Base64 encoded image data
        chart_type_hint: Optional hint about chart type (bar, line, pie, etc.)
        
    Returns:
        Structured data dictionary
    """
    try:
        chart_specific_prompt = f"""
        Analyze this {chart_type_hint + ' ' if chart_type_hint else ''}chart/graph and extract the data in a structured format.

        Return the information as:
        - Chart Type: [bar chart/line graph/pie chart/table/etc.]
        - Title: [exact title]
        - X-axis: [label and values]
        - Y-axis: [label and values] 
        - Data Series: [list each series with values]
        - Time Period: [if applicable]
        - Key Trends: [main patterns]
        - Highest/Lowest Values: [notable peaks/troughs]

        Be precise with numbers and labels. If text is unclear, indicate [unclear] but extract what you can see clearly.
        """

        message = HumanMessage(
            content=[
                {"type": "text", "text": chart_specific_prompt},
                {
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                }
            ]
        )

        response = await vision_llm.ainvoke([message])
        
        # Parse the response into structured data
        content = response.content.strip()
        
        # For now, return as text, but this could be parsed into a proper dict
        return {
            "structured_analysis": content,
            "chart_type": chart_type_hint or "unknown",
            "analysis_method": "gemini_vision"
        }
        
    except Exception as e:
        logger.error(f"Error in structured chart analysis: {e}")
        return {
            "error": str(e),
            "chart_type": chart_type_hint or "unknown",
            "analysis_method": "failed"
        }