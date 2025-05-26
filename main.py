import json 
from typing import List, Dict
from crewai import Agent, Task, Crew, LLM
from crewai.flow.flow import Flow, start, listen
from pydantic import BaseModel, Field
from src.researcher_content.crews.content_crew.content_crew import ContentCrew
import os 
from dotenv import load_dotenv

class Section(BaseModel):
    title: str = Field(description="The title of the section")
    description: str = Field(description="Brief description of what the section should cover")
    
class GuideOutline(BaseModel):
    title: str = Field(description="The title of the guide")
    introduction: str = Field(description="Introduction to the topic")
    target_audience: str = Field(description="The target audience for the guide")
    sections: List[Section] = Field(description="List of sections that make up the guide")
    conclusion: str = Field(description="Conclusion or Summary of the guide")
    
# Define our flow state
class GuideCreatorState(BaseModel):
    topic: str = ""
    audience_level: str = ""
    guide_outline: GuideOutline = None
    sections_content: Dict[str, str] = {}
    
class GuideCreatorFlow(Flow[GuideCreatorState]):
    """Flow for creating a guide"""
    
    @start()
    def get_user_input(self):
        """Get user input for topic and audience level"""
        print("\n=== Create your Comprenhensive Guide ===")
        
        # Get the user input
        self.state.topic = input("Enter the topic of the guide: ")
        
        # Get audience level with validation
        while True: 
            auidence = input("Enter the target audience level (beginner, intermediate, advanced): ").lower()
            if auidence in ["beginner", "intermediate", "advanced"]:
                self.state.audience_level = auidence
                break
            else:
                print("Invalid audience level. Please choose from beginner, intermediate, or advanced.")
                
        print(f"\nCreating a guide on {self.state.topic} for {self.state.audience_level} audience...\n")
        return self.state
    
    @listen(get_user_input)
    def create_guide_outline(self, state):
        """Create a structured outline for the guide using a direct LLM call"""
        print("Creating guide outline...")

        load_dotenv()
        os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
        # Initialize the LLM
        llm = LLM(model="gpt-4o-mini", response_format=GuideOutline)

        # Create the messages for the outline
        messages = [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": f"""
            Create a detailed outline for a comprehensive guide on "{state.topic}" for {state.audience_level} level learners.

            The outline should include:
            1. A compelling title for the guide
            2. An introduction to the topic
            3. 1 main sections that cover the most important aspects of the topic
            4. A conclusion or summary

            For each section, provide a clear title and a brief description of what it should cover.
            """}
        ]

        # Make the LLM call with JSON response format
        response = llm.call(messages=messages)

        # Parse the JSON response
        outline_dict = json.loads(response)
        self.state.guide_outline = GuideOutline(**outline_dict)

        # Save the outline to a file
        with open("output/guide_outline.json", "w") as f:
            json.dump(outline_dict, f, indent=2)

        print(f"Guide outline created with {len(self.state.guide_outline.sections)} sections")
        return self.state.guide_outline

    @listen(create_guide_outline)
    def write_and_compile_guide(self, outline):
        """Write and compile the guide"""
        print("\n=== Writing and compiling the guide ===")
        completed_sections = []
        
        for section in outline.sections:
            print(f"\n=== Processing section: {section.title} ===")
            
            # Build context from previous sections
            previous_sections_text = ""
            if completed_sections:
                previous_sections_text = "# Previously Written Sections\n\n"
                for title in completed_sections:
                    previous_sections_text += f"## {title}\n\n"
                    previous_sections_text += self.state.sections_content.get(title, "") + "\n\n"
            else:
                previous_sections_text = "No previous sections written yet."
                
            # Run the crew
            result = ContentCrew().crew().kickoff(inputs={
                "section_title": section.title,
                "section_description": section.description,
                "audience_level": self.state.audience_level,
                "previous_sections": previous_sections_text,
                "draft_content": ""
            })
            
            # Store the content
            self.state.sections_content[section.title] = result.raw
            completed_sections.append(section.title)
            print(f"Section completed: {section.title}")
        
        # Compile the final guide
        guide_content = f"# {outline.title}\n\n"
        guide_content += f"## Introduction\n\n{outline.introduction}\n\n"

        # Add each section in order
        for section in outline.sections:
            section_content = self.state.sections_content.get(section.title, "")
            guide_content += f"\n\n{section_content}\n\n"

        # Add conclusion
        guide_content += f"## Conclusion\n\n{outline.conclusion}\n\n"

        # Save the guide
        with open("output/complete_guide.md", "w") as f:
            f.write(guide_content)

        print("\nComplete guide compiled and saved to output/complete_guide.md")
        return "Guide creation completed successfully"
    
def kickoff():
    """Run the guide creator flow"""
    flow = GuideCreatorFlow()
    flow.kickoff()
    print("\n=== Flow Complete ===")
    print("Your comprehensive guide is ready in the output directory.")
    print("Open output/complete_guide.md to view it.")
    
def plot():
    """Generate a visualization of the flow"""
    flow = GuideCreatorFlow()
    flow.plot("guide_creator_flow")
    print("Flow visulization saved to guide_creator_flow.html")
    
if __name__ == "__main__":
    kickoff()
    plot()

            
       
            
        