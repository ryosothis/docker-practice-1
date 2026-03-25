from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)


# Трекер привычек API (4 задание)

habits = []
next_habit_id = 1
habit_checks = []  # Список отметок выполнения

def get_current_streak(habit_id):
    """Вычисляет текущую серию (streak) выполнения привычки"""
    # Получаем все отметки для привычки
    checks = [c for c in habit_checks if c["habit_id"] == habit_id]
    
    if not checks:
        return 0
    
    # Сортируем отметки по дате (от новых к старым)
    sorted_checks = sorted(checks, key=lambda x: x["date"], reverse=True)
    
    today = datetime.now().date()
    streak = 0
    expected_date = today
    
    # Проверяем последовательные дни начиная с сегодня
    for check in sorted_checks:
        check_date = datetime.strptime(check["date"], "%Y-%m-%d").date()
        
        # Если проверка за сегодня
        if check_date == expected_date:
            streak += 1
            expected_date -= timedelta(days=1)
        # Если пропущен день
        elif check_date < expected_date:
            break
        # Если есть проверка за будущий день (игнорируем)
        elif check_date > expected_date:
            continue
        else:
            break
    
    return streak

@app.route("/habits", methods=["GET"])
def get_habits():
    """Получить список всех привычек"""
    return jsonify(habits)

@app.route("/habits", methods=["POST"])
def create_habit():
    """Создать новую привычку"""
    global next_habit_id
    data = request.get_json()
    
    if not data or "name" not in data or "user_id" not in data:
        return jsonify({"error": "Missing required fields: name, user_id"}), 400
    
    habit = {
        "id": next_habit_id,
        "name": data["name"],
        "user_id": data["user_id"],
        "created_at": datetime.now().isoformat()
    }
    habits.append(habit)
    next_habit_id += 1
    
    return jsonify(habit), 201

@app.route("/habits/<int:habit_id>/check", methods=["POST"])
def check_habit(habit_id):
    """Отметить выполнение привычки за определенную дату"""
    data = request.get_json()
    
    if not data or "date" not in data:
        return jsonify({"error": "Missing required field: date"}), 400
    
    # Проверяем существование привычки
    habit = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        return jsonify({"error": "Habit not found"}), 404
    
    # Проверяем формат даты
    try:
        check_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    # Проверяем, не существует ли уже отметка за эту дату
    existing_check = next(
        (c for c in habit_checks 
         if c["habit_id"] == habit_id and c["date"] == data["date"]), 
        None
    )
    
    if existing_check:
        return jsonify({"error": "Check already exists for this date"}), 409
    
    # Создаем новую отметку
    habit_check = {
        "id": len(habit_checks) + 1,
        "habit_id": habit_id,
        "date": data["date"],
        "checked_at": datetime.now().isoformat()
    }
    habit_checks.append(habit_check)
    
    return jsonify({
        "message": "Habit checked successfully",
        "check": habit_check
    }), 201

@app.route("/habits/<int:habit_id>/streak", methods=["GET"])
def get_streak(habit_id):
    """Получить текущую серию выполнения привычки"""
    # Проверяем существование привычки
    habit = next((h for h in habits if h["id"] == habit_id), None)
    
    if not habit:
        return jsonify({"error": "Habit not found"}), 404
    
    streak = get_current_streak(habit_id)
    
    return jsonify({
        "habit_id": habit_id,
        "habit_name": habit["name"],
        "current_streak": streak
    }), 200

# Дополнительный эндпоинт для получения всех отметок (для отладки)
@app.route("/habits/<int:habit_id>/checks", methods=["GET"])
def get_habit_checks(habit_id):
    """Получить все отметки привычки (для отладки)"""
    checks = [c for c in habit_checks if c["habit_id"] == habit_id]
    return jsonify(checks)

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)