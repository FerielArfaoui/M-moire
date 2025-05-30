from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

app = FastAPI()

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginData(BaseModel):
    email: EmailStr
    password: str

admins = {
    "admin1@example.com": {"password": "pass1", "dashboards": ["http://localhost:8050", "http://localhost:8051"]},
    "admin2@example.com": {"password": "pass2", "dashboards": ["http://localhost:8050", "http://localhost:8051"]},
    "admin3@example.com": {"password": "pass3", "dashboards": ["http://localhost:8050", "http://localhost:8051"]},
    "admin4@example.com": {"password": "pass4", "dashboards": ["http://localhost:8050", "http://localhost:8051"]},
    "admin5@example.com": {"password": "pass5", "dashboards": ["http://localhost:8050", "http://localhost:8051"]},
    "admin6@example.com": {"password": "pass6", "dashboards": ["http://localhost:8050", "http://localhost:8051"]},
    "admin7@example.com": {"password": "pass7", "dashboards": ["http://localhost:8050", "http://localhost:8051"]},
    "admin8@example.com": {"password": "pass8", "dashboards": ["http://localhost:8050", "http://localhost:8051"]},
    "admin9@example.com": {"password": "pass9", "dashboards": ["http://localhost:8050", "http://localhost:8051"]},
    "admin10@example.com": {"password": "pass10", "dashboards": ["http://localhost:8050", "http://localhost:8051"]},
}

@app.post("/login")
async def login(data: LoginData):
    admin = admins.get(data.email)
    if admin and admin["password"] == data.password:
        return {"message": "Connexion réussie !", "dashboards": admin["dashboards"]}
    else:
        raise HTTPException(status_code=401, detail="Identifiants invalides")

@app.get("/")
async def root():
    return {"message": "Backend FastAPI en marche"}
