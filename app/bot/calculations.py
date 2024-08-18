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
        bill_distance = int(load_criteria["billDistance"].replace(' miles', '').strip())
        weight = int(load_criteria["weight"].replace(' lbs', '').replace(',', '').strip())
        driver_assistance = load_criteria["driverAssistance"]
        trailer_type = load_criteria["equipmentType"].upper()
        
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
        equipment_base_rate = {
            'V': 1.45,   # Van
            'R': 1.60,   # Reefer
            'F': 1.75,   # Flatbed
            'VR': 1.70,  # Van/Reefer
            'FT': 1.80,  # Flatbed with Tarps
            'FR': 1.85,  # Flatbed with Reefer
            'F/FT': 1.90,# Flatbed with Tarps
            'F/R': 1.95, # Flatbed with Reefer
            'D': 1.50,   # Dry van
            'P': 1.65    # Power only
        }

        base_rate = bill_distance * equipment_base_rate.get(trailer_type, 1.45)  # Default to 1.45 if unknown
        
        if base_rate < 350:
            base_rate = 350
            
        total_rate = base_rate + (bill_distance * 0.5)
        
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
