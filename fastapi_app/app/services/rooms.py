"""Room selection and scope validation shared by event operations."""
from fastapi import HTTPException
from ..models.event import EventRoom


def require_room(db, event_id, room_id, required=False):
    if room_id is not None and room_id < 0:
        raise HTTPException(422, 'Invalid room')
    if not room_id:
        if required and db.query(EventRoom.id).filter_by(event_id=event_id).first():
            raise HTTPException(409, 'Choose a room before placing this order')
        return None
    room = db.query(EventRoom).filter_by(id=room_id, event_id=event_id).first()
    if not room:
        raise HTTPException(404, 'Room not found in this event')
    return room


def room_filter(query, model, room_id):
    if room_id is None:
        return query
    return query.filter(model.room_id == (room_id or None))


def check_order_room(order, room_id):
    if room_id is not None and order.room_id != (room_id or None):
        raise HTTPException(409, 'This order belongs to another room. Refresh the selected room.')
