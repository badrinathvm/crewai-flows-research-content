from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, task, crew
import os
from dotenv import load_dotenv

@CrewBase
class ContentCrew():
    """Content writing crew"""
    
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
   
    def __init__(self):
        load_dotenv()
        os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
        self.groq_llm = LLM(model="groq/qwen-qwq-32b")
        self.llama = LLM(
            model="ollama/llama3.2:latest",
            base_url="http://127.0.0.1:11434")

    
    @agent
    def content_writer(self) -> Agent:
        """Content writer agent"""
        return Agent(
            config=self.agents_config['content_writer'],
            llm= self.llama,
            verbose=True
        )
        
    @agent
    def content_reviewer(self) -> Agent:
        """Content reviewer agent"""
        return Agent(
            config=self.agents_config['content_reviewer'],
            llm=self.llama,
            verbose=True
        )
        
    @task
    def write_section_task(self) -> Task:
        """Write section task"""
        return Task(
            config=self.tasks_config['write_section_task']
        )
        
    @task
    def review_section_task(self) -> Task:
        """Review section task"""
        return Task(
            config=self.tasks_config['review_section_task'],
            context=[self.write_section_task()]
        )
        
    @crew
    def crew(self) -> Crew:
        """Content crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )