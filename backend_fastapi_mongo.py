
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from pymongo import MongoClient
from bson.objectid import ObjectId

app = FastAPI()

# Conexión a MongoDB Atlas
MONGO_URI = "mongodb+srv://gptuser:<db_password>@tareas-gpt.rv6obcy.mongodb.net/?retryWrites=true&w=majority&appName=tareas-gpt"
client = MongoClient(MONGO_URI)
db = client["tareasdb"]
tareas_collection = db["tareas"]

# Modelos de entrada y salida
class TareaIn(BaseModel):
    descripcion: str
    responsable: Optional[str] = None
    vencimiento: Optional[date] = None
    estado: Optional[str] = "pendiente"

class TareaOut(TareaIn):
    id: str

# Crear una nueva tarea
@app.post("/tareas", response_model=TareaOut)
def crear_tarea(tarea: TareaIn):
    tarea_dict = tarea.dict()
    result = tareas_collection.insert_one(tarea_dict)
    tarea_out = {**tarea_dict, "id": str(result.inserted_id)}
    return tarea_out

# Listar tareas
@app.get("/tareas", response_model=List[TareaOut])
def listar_tareas(estado: Optional[str] = None):
    query = {}
    if estado:
        query["estado"] = estado
    tareas = []
    for t in tareas_collection.find(query):
        t["id"] = str(t["_id"])
        del t["_id"]
        tareas.append(t)
    return tareas

# Cambiar estado de una tarea
@app.patch("/tareas/{tarea_id}", response_model=TareaOut)
def actualizar_estado(tarea_id: str, nuevo_estado: str):
    result = tareas_collection.find_one_and_update(
        {"_id": ObjectId(tarea_id)},
        {"$set": {"estado": nuevo_estado}},
        return_document=True
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    result["id"] = str(result["_id"])
    del result["_id"]
    return result
