from uuid import UUID

from pydantic import BaseModel, Field

TECH_FIELDS = [
    "Backend Engineering",
    "Frontend Engineering",
    "Full Stack Engineering",
    "Machine Learning / AI",
    "Data Science / Analytics",
    "DevOps / SRE / Platform",
    "Mobile Engineering",
    "Security Engineering",
    "Embedded / Systems Engineering",
    "Cloud Architecture",
    "QA / Test Engineering",
    "Data Engineering",
]

TECH_STACKS_BY_FIELD: dict[str, list[str]] = {
    "Backend Engineering": [
        "Python", "Node.js", "Go", "Java", "Rust", "C#", "Ruby",
        "FastAPI", "Django", "Flask", "Express", "Spring Boot", "NestJS",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka", "RabbitMQ",
        "Docker", "Kubernetes", "gRPC", "REST APIs", "GraphQL",
    ],
    "Frontend Engineering": [
        "TypeScript", "JavaScript", "React", "Next.js", "Vue.js", "Angular", "Svelte",
        "HTML/CSS", "Tailwind CSS", "Sass", "Webpack", "Vite",
        "React Query", "Redux", "Zustand", "Jest", "Cypress", "Playwright",
        "Figma", "Storybook", "GraphQL",
    ],
    "Full Stack Engineering": [
        "TypeScript", "JavaScript", "Python", "Node.js", "React", "Next.js",
        "FastAPI", "Express", "PostgreSQL", "MongoDB", "Redis",
        "Docker", "AWS", "Tailwind CSS", "GraphQL", "REST APIs",
    ],
    "Machine Learning / AI": [
        "Python", "PyTorch", "TensorFlow", "JAX", "scikit-learn",
        "HuggingFace Transformers", "LangChain", "LlamaIndex",
        "pandas", "NumPy", "OpenCV", "CUDA", "MLflow", "Weights & Biases",
        "AWS SageMaker", "Vertex AI", "ONNX",
    ],
    "Data Science / Analytics": [
        "Python", "SQL", "R", "pandas", "NumPy", "scikit-learn",
        "dbt", "Airflow", "Spark", "Snowflake", "BigQuery", "Redshift",
        "Tableau", "Power BI", "Looker", "Jupyter", "Matplotlib", "Plotly",
    ],
    "DevOps / SRE / Platform": [
        "Docker", "Kubernetes", "Terraform", "Helm", "ArgoCD", "GitOps",
        "AWS", "GCP", "Azure", "GitHub Actions", "Jenkins", "CircleCI",
        "Prometheus", "Grafana", "Datadog", "OpenTelemetry",
        "Ansible", "Pulumi", "Linux", "Bash", "Python",
    ],
    "Mobile Engineering": [
        "React Native", "Expo", "Swift", "SwiftUI", "Objective-C",
        "Kotlin", "Java (Android)", "Flutter", "Dart",
        "Firebase", "SQLite", "REST APIs", "GraphQL",
        "App Store / Play Store", "TestFlight",
    ],
    "Security Engineering": [
        "Python", "Go", "C", "Bash",
        "OWASP", "Penetration Testing", "SAST/DAST", "Burp Suite",
        "AWS Security", "IAM", "Zero Trust", "SOC 2", "ISO 27001",
        "SIEM", "Splunk", "Vault", "PKI / mTLS",
    ],
    "Embedded / Systems Engineering": [
        "C", "C++", "Rust", "Assembly", "Python",
        "RTOS", "FreeRTOS", "Linux Kernel", "Device Drivers",
        "ARM Cortex", "RISC-V", "FPGA", "VHDL/Verilog",
        "CAN Bus", "SPI/I2C/UART", "CMake", "GDB",
    ],
    "Cloud Architecture": [
        "AWS", "GCP", "Azure", "Terraform", "Pulumi", "CDK",
        "Kubernetes", "Serverless", "Lambda", "Cloud Run",
        "Networking / VPC", "IAM", "Cost Optimization",
        "Multi-cloud", "DR / HA Design", "FinOps",
    ],
    "QA / Test Engineering": [
        "Python", "JavaScript", "TypeScript",
        "Selenium", "Playwright", "Cypress", "Appium",
        "JMeter", "k6", "Postman", "REST Assured",
        "pytest", "Jest", "JUnit", "TestNG",
        "CI/CD", "BDD", "Allure",
    ],
    "Data Engineering": [
        "Python", "SQL", "Scala", "Java",
        "Apache Spark", "Flink", "Kafka", "Airflow", "Prefect",
        "dbt", "Snowflake", "BigQuery", "Redshift", "Delta Lake",
        "Iceberg", "AWS Glue", "Databricks", "Great Expectations",
    ],
}


class SkillIn(BaseModel):
    name: str = Field(max_length=120)
    category: str = Field(max_length=64)
    proficiency: str | None = Field(default=None, max_length=64)
    years: float | None = None


class ExperienceIn(BaseModel):
    company: str = Field(max_length=180)
    title: str = Field(max_length=180)
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    achievements: list[str] = []


class EducationIn(BaseModel):
    institution: str = Field(max_length=180)
    degree: str | None = Field(default=None, max_length=180)
    field: str | None = Field(default=None, max_length=180)
    start_date: str | None = None
    end_date: str | None = None


class ProjectIn(BaseModel):
    name: str = Field(max_length=180)
    description: str | None = None
    skills: list[str] = []
    links: list[str] = []


class ProfileUpdate(BaseModel):
    years_experience: float | None = None
    seniority: str | None = Field(default=None, max_length=64)
    field: str | None = Field(default=None, max_length=120)
    tech_stacks: list[str] = []
    domain_expertise: list[str] = []
    preferred_roles: list[str] = []
    industries: list[str] = []
    ats_keywords: list[str] = []
    location_preferences: dict = {}
    work_authorization: dict = {}
    summary: str | None = None
    skills: list[SkillIn] = []
    experience: list[ExperienceIn] = []
    education: list[EducationIn] = []
    projects: list[ProjectIn] = []


class SkillOut(BaseModel):
    name: str
    category: str
    proficiency: str | None
    years: float | None

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    years_experience: float | None = None
    seniority: str | None = None
    field: str | None = None
    tech_stacks: list[str] = []
    domain_expertise: list[str] = []
    preferred_roles: list[str] = []
    industries: list[str] = []
    ats_keywords: list[str] = []
    location_preferences: dict = {}
    work_authorization: dict = {}
    summary: str | None = None
    skills: list[SkillOut] = []

    class Config:
        from_attributes = True
