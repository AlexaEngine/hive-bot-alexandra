from pymongo import MongoClient
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
                    'Shipper city': {'$eq': load_criteria['shipperCity'].upper()},
                    'Consignee city': {'$eq': load_criteria['consigneeCity'].upper()},
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
                        '$gte': load_criteria['billDistance'] - distance_tolerance,
                        '$lte': load_criteria['billDistance'] + distance_tolerance
                    },
                    'normalizedWeight': {
                        '$gte': load_criteria['weight'] - weight_tolerance,
                        '$lte': load_criteria['weight'] + weight_tolerance
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
            average_rate = float(result[0]['averageRate'].to_decimal()) * 1.06
            message = f"The estimated rate based on historically similar loads is: ${average_rate:.2f}"
        else:
            distance = load_criteria.get("billDistance", 0)
            equipment_type_code = load_criteria.get("Equipment Type", 'V')
            multiplier = EQUIPMENT_TYPE_MULTIPLIERS.get(equipment_type_code, 1)
            base_rate = distance * 1.45 * multiplier
            
            if base_rate < 350:
                base_rate = 350
            
            total_rate = base_rate + (distance * 0.5)
            
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