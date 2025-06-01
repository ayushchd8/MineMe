from flask import Blueprint, jsonify, request, current_app
from ..models import SalesforceObject
from ..services import SyncService

objects_bp = Blueprint('objects', __name__, url_prefix='/api/objects')

@objects_bp.route('/', methods=['GET'])
def get_objects():
    """Get all registered Salesforce objects."""
    objects = SalesforceObject.get_all()
    return jsonify({
        'objects': [
            {
                'id': obj.id,
                'name': obj.name,
                'api_name': obj.api_name,
                'description': obj.description,
                'is_active': obj.is_active,
                'last_sync_time': obj.last_sync_time.isoformat() if obj.last_sync_time else None
            }
            for obj in objects
        ]
    })

@objects_bp.route('/<int:object_id>', methods=['GET'])
def get_object(object_id):
    """Get a specific Salesforce object by ID."""
    obj = SalesforceObject.get_by_id(object_id)
    
    if not obj:
        return jsonify({'error': 'Object not found'}), 404
    
    return jsonify({
        'id': obj.id,
        'name': obj.name,
        'api_name': obj.api_name,
        'description': obj.description,
        'is_active': obj.is_active,
        'last_sync_time': obj.last_sync_time.isoformat() if obj.last_sync_time else None
    })

@objects_bp.route('/', methods=['POST'])
def register_object():
    """Register a new Salesforce object for synchronization."""
    data = request.json
    
    if not data or 'api_name' not in data:
        return jsonify({'error': 'API name is required'}), 400
    
    # Create sync service
    sync_service = SyncService(config=current_app.config)
    
    # Register the object
    obj = sync_service.register_object(data['api_name'])
    
    if not obj:
        return jsonify({'error': 'Failed to register object'}), 400
    
    return jsonify({
        'id': obj.id,
        'name': obj.name,
        'api_name': obj.api_name,
        'description': obj.description,
        'is_active': obj.is_active
    }), 201

@objects_bp.route('/<int:object_id>', methods=['PUT'])
def update_object(object_id):
    """Update a Salesforce object's properties."""
    obj = SalesforceObject.get_by_id(object_id)
    
    if not obj:
        return jsonify({'error': 'Object not found'}), 404
    
    data = request.json
    
    if 'name' in data:
        obj.name = data['name']
    
    if 'description' in data:
        obj.description = data['description']
    
    if 'is_active' in data:
        obj.is_active = data['is_active']
    
    obj.save()
    
    return jsonify({
        'id': obj.id,
        'name': obj.name,
        'api_name': obj.api_name,
        'description': obj.description,
        'is_active': obj.is_active,
        'last_sync_time': obj.last_sync_time.isoformat() if obj.last_sync_time else None
    })

@objects_bp.route('/<int:object_id>', methods=['DELETE'])
def delete_object(object_id):
    """Delete a Salesforce object."""
    obj = SalesforceObject.get_by_id(object_id)
    
    if not obj:
        return jsonify({'error': 'Object not found'}), 404
    
    obj.delete()
    
    return jsonify({'message': 'Object deleted successfully'}) 