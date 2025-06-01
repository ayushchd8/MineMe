from flask import Blueprint, jsonify, request
from ..models import SalesforceObject, SalesforceRecord

records_bp = Blueprint('records', __name__, url_prefix='/api/records')

@records_bp.route('/object/<int:object_id>', methods=['GET'])
def get_records_by_object(object_id):
    """Get records for a specific Salesforce object."""
    # Check if object exists
    obj = SalesforceObject.get_by_id(object_id)
    if not obj:
        return jsonify({'error': 'Object not found'}), 404
    
    # Get query parameters
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int, default=0)
    
    # Get records
    records = SalesforceRecord.get_by_object_id(object_id, include_deleted)
    
    # Apply pagination if limit is specified
    if limit is not None:
        records = records[offset:offset + limit]
    
    return jsonify({
        'object': {
            'id': obj.id,
            'name': obj.name,
            'api_name': obj.api_name
        },
        'records': [
            {
                'id': record.id,
                'sf_id': record.sf_id,
                'data': record.data_dict,
                'last_modified_date': record.last_modified_date.isoformat() if record.last_modified_date else None,
                'is_deleted': record.is_deleted
            }
            for record in records
        ],
        'total': len(records),
        'offset': offset,
        'limit': limit
    })

@records_bp.route('/<string:sf_id>', methods=['GET'])
def get_record_by_sf_id(sf_id):
    """Get a specific record by its Salesforce ID."""
    record = SalesforceRecord.get_by_sf_id(sf_id)
    
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    
    obj = SalesforceObject.get_by_id(record.object_id)
    
    return jsonify({
        'id': record.id,
        'sf_id': record.sf_id,
        'object': {
            'id': obj.id,
            'name': obj.name,
            'api_name': obj.api_name
        },
        'data': record.data_dict,
        'last_modified_date': record.last_modified_date.isoformat() if record.last_modified_date else None,
        'is_deleted': record.is_deleted
    })

@records_bp.route('/search', methods=['GET'])
def search_records():
    """Search for records across all objects or within a specific object."""
    # Get query parameters
    query = request.args.get('q', '')
    object_id = request.args.get('object_id', type=int)
    limit = request.args.get('limit', type=int, default=20)
    
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    # Initialize results
    results = []
    
    # If object_id is specified, search only within that object
    if object_id:
        obj = SalesforceObject.get_by_id(object_id)
        if not obj:
            return jsonify({'error': 'Object not found'}), 404
        
        records = SalesforceRecord.get_by_object_id(object_id)
        
        # Simple search implementation (could be improved with full-text search)
        for record in records:
            if any(query.lower() in str(value).lower() for value in record.data_dict.values()):
                results.append({
                    'id': record.id,
                    'sf_id': record.sf_id,
                    'object': {
                        'id': obj.id,
                        'name': obj.name,
                        'api_name': obj.api_name
                    },
                    'data': record.data_dict
                })
                
                if len(results) >= limit:
                    break
    else:
        # Search across all objects
        objects = SalesforceObject.get_all()
        
        for obj in objects:
            records = SalesforceRecord.get_by_object_id(obj.id)
            
            for record in records:
                if any(query.lower() in str(value).lower() for value in record.data_dict.values()):
                    results.append({
                        'id': record.id,
                        'sf_id': record.sf_id,
                        'object': {
                            'id': obj.id,
                            'name': obj.name,
                            'api_name': obj.api_name
                        },
                        'data': record.data_dict
                    })
                    
                    if len(results) >= limit:
                        break
            
            if len(results) >= limit:
                break
    
    return jsonify({
        'query': query,
        'results': results,
        'count': len(results)
    }) 