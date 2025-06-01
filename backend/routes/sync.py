from flask import Blueprint, jsonify, request, current_app
from ..models import SalesforceObject, SyncLog
from ..services import SyncService

sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')

@sync_bp.route('/status', methods=['GET'])
def get_sync_status():
    """Get the current synchronization status."""
    # Get latest sync log for each object
    objects = SalesforceObject.get_all()
    
    status = []
    for obj in objects:
        latest_log = SyncLog.query.filter_by(object_id=obj.id).order_by(SyncLog.start_time.desc()).first()
        
        status.append({
            'object': {
                'id': obj.id,
                'name': obj.name,
                'api_name': obj.api_name
            },
            'last_sync_time': obj.last_sync_time.isoformat() if obj.last_sync_time else None,
            'latest_sync': {
                'id': latest_log.id,
                'type': latest_log.sync_type,
                'status': latest_log.status,
                'start_time': latest_log.start_time.isoformat(),
                'end_time': latest_log.end_time.isoformat() if latest_log.end_time else None,
                'records_processed': latest_log.records_processed,
                'records_created': latest_log.records_created,
                'records_updated': latest_log.records_updated,
                'records_deleted': latest_log.records_deleted,
                'error_message': latest_log.error_message
            } if latest_log else None
        })
    
    return jsonify({
        'objects': status
    })

@sync_bp.route('/logs', methods=['GET'])
def get_sync_logs():
    """Get synchronization logs."""
    # Get query parameters
    object_id = request.args.get('object_id', type=int)
    limit = request.args.get('limit', type=int, default=20)
    offset = request.args.get('offset', type=int, default=0)
    
    # Build query
    query = SyncLog.query
    
    if object_id:
        query = query.filter_by(object_id=object_id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    logs = query.order_by(SyncLog.start_time.desc()).offset(offset).limit(limit).all()
    
    return jsonify({
        'logs': [
            {
                'id': log.id,
                'object_id': log.object_id,
                'object_name': log.object.name if log.object else None,
                'type': log.sync_type,
                'status': log.status,
                'start_time': log.start_time.isoformat(),
                'end_time': log.end_time.isoformat() if log.end_time else None,
                'records_processed': log.records_processed,
                'records_created': log.records_created,
                'records_updated': log.records_updated,
                'records_deleted': log.records_deleted,
                'error_message': log.error_message
            }
            for log in logs
        ],
        'total': total,
        'offset': offset,
        'limit': limit
    })

@sync_bp.route('/object/<int:object_id>', methods=['POST'])
def sync_object(object_id):
    """Trigger synchronization for a specific object."""
    # Check if object exists
    obj = SalesforceObject.get_by_id(object_id)
    if not obj:
        return jsonify({'error': 'Object not found'}), 404
    
    # Get sync type
    data = request.json or {}
    sync_type = data.get('type', 'incremental')
    
    if sync_type not in ['full', 'incremental']:
        return jsonify({'error': 'Invalid sync type. Must be "full" or "incremental"'}), 400
    
    # Create sync service
    sync_service = SyncService(config=current_app.config)
    
    # Trigger sync
    result = sync_service.sync_object(object_id=object_id, sync_type=sync_type)
    
    if not result:
        return jsonify({'error': 'Sync failed'}), 500
    
    return jsonify({
        'success': True,
        'object_id': object_id,
        'sync_type': sync_type,
        'result': result
    })

@sync_bp.route('/all', methods=['POST'])
def sync_all_objects():
    """Trigger synchronization for all active objects."""
    # Get sync type
    data = request.json or {}
    sync_type = data.get('type', 'incremental')
    
    if sync_type not in ['full', 'incremental']:
        return jsonify({'error': 'Invalid sync type. Must be "full" or "incremental"'}), 400
    
    # Get active objects
    objects = SalesforceObject.get_active_objects()
    
    if not objects:
        return jsonify({'error': 'No active objects found'}), 404
    
    # Create sync service
    sync_service = SyncService(config=current_app.config)
    
    # Trigger sync for each object
    results = []
    for obj in objects:
        result = sync_service.sync_object(object_id=obj.id, sync_type=sync_type)
        
        results.append({
            'object_id': obj.id,
            'object_name': obj.name,
            'success': result is not None,
            'result': result
        })
    
    return jsonify({
        'success': True,
        'sync_type': sync_type,
        'results': results
    }) 