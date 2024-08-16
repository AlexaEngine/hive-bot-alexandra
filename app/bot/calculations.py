from pymongo import MongoClient, errors
from app.config import MONGO_CLIENT, EQUIPMENT_TYPE_MULTIPLIERS

async def calculate_approximate_rate_quote(load_criteria: dict, update, context):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        distance_tolerance = 60
        weight_tolerance = 3500
        
        hazmat_routing = load_criteria.get("hazmatRouting", "No").upper()
        shipper_city = load_criteria["shipperCity"]
        consignee_city = load_criteria["consigneeCity"]
        bill_distance = load_criteria["billDistance"]
        weight = load_criteria["weight"]
        driver_assistance = load_criteria["driverAssistance"]
        trailer_type = load_criteria["equipmentType"]
        
        pipeline = [
            {
                '$match': {
                    'Shipper city': {'$eq': shipper_city.upper()},
                    'Consignee city': {'$eq': consignee_city.upper()},
                    'Bill Distance': {'$exists': True, '$ne': None},
                    'Weight': {'$exists': True, '$ne': None}
                }
            },
            {
                '$addFields': {
                    'normalizedBillDistance': {
                        '$cond': {
                            'if': {'$eq': [{'$type': '$Bill Distance'}, 'undefined']},
                            'then': 0,
                            'else': {'$toDouble': '$Bill Distance'}
                        }
                    },
                    'normalizedWeight': {
                        '$cond': {
                            'if': {'$eq': [{'$type': '$Weight'}, 'undefined']},
                            'then': 0,
                            'else': {'$toDouble': '$Weight'}
                        }
                    }
                }
            },
            {
                '$match': {
                    'normalizedBillDistance': {
                        '$gte': bill_distance - distance_tolerance,
                        '$lte': bill_distance + distance_tolerance
                    },
                    'normalizedWeight': {
                        '$gte': weight - weight_tolerance,
                        '$lte': weight + weight_tolerance
                    }
                }
            },
            {
                '$group': {
                    '_id': None,
                    'averageRate': {'$avg': '$Rate'}
                }
            }
        ]
      
        client = MongoClient(MONGO_CLIENT)
        db = client['hivedb']
        data = db['hive-cx-data']
        cursor = data.aggregate(pipeline, maxTimeMS=90000)
        result = list(cursor)
        
        if result and 'averageRate' in result[0]:
            average_rate = float(result[0]['averageRate']) * 1.06
            message = f"The estimated rate based on historically similar loads is: ${average_rate:.2f}"
        else:
            raise ValueError("No matching historical data found")
    
    except (errors.PyMongoError, ValueError) as e:
        # If MongoDB fails or no matching data, calculate using the formula
        base_rate = bill_distance * 1.45 * EQUIPMENT_TYPE_MULTIPLIERS.get(trailer_type, 1)
        
        if base_rate < 350:
            base_rate = 350
            
        total_rate = base_rate + (bill_distance * 0.8)
        
        if driver_assistance == 'Yes':
            total_rate += 100
        if hazmat_routing == 'Yes':
            total_rate += 200
        if load_criteria.get("driverAssistance", 'No') == 'Yes':
            total_rate += 100
        if load_criteria.get("Tolls", 'No') == 'Yes':
            total_rate += 50
            
        message = f"Based on my analysis and calculations of the information provided, the estimated rate is: ${total_rate:.2f}"
    
    except Exception as e:
        message = f"Sorry, I couldn't process that rate due to an error: {e}"
        
    return message
