from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# app = FastAPI()

app = FastAPI(
    title="Tareas API",
    version="1.0.0",
    servers=[{
        "url": "https://tareas-api.onrender.com"
    }])

# Conexión a MongoDB Atlas
MONGO_URI = "mongodb+srv://gptuser:Guratinian0@tareas-gpt.rv6obcy.mongodb.net/?retryWrites=true&w=majority&appName=tareas-gpt"
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
    # antes de insertar en la base de datos:
    if isinstance(tarea.vencimiento,
                  date):  # opcionalmente importa `date` de datetime
        tarea.vencimiento = datetime.combine(tarea.vencimiento,
                                             datetime.min.time())

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


class UpdateTareaModel(BaseModel):
    updates: Dict[str, Any]


@app.patch("/tareas/{tarea_id}")
def actualizar_campo_tarea(tarea_id: str, updates: dict = Body(...)):
    result = tareas_collection.find_one_and_update({"_id": ObjectId(tarea_id)},
                                                   {"$set": updates},
                                                   return_document=True)
    if not result:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    result["id"] = str(result["_id"])
    del result["_id"]
    return result


@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: str):
    result = tareas_collection.delete_one({"_id": ObjectId(tarea_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return {"message": "Tarea eliminada correctamente"}
