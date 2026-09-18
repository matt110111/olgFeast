from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, UniqueConstraint
from sqlalchemy.sql import func
from ..core.database import Base


class DinnerEvent(Base):
    __tablename__ = 'dinner_events'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    event_date = Column(String(10), nullable=False)
    closed = Column(Boolean, nullable=False, default=False)
    collect_tickets = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EventRoom(Base):
    __tablename__ = 'event_rooms'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('dinner_events.id'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    __table_args__ = (UniqueConstraint('event_id', 'name', name='uq_event_room_name'),)


class RoomMenuItem(Base):
    __tablename__ = 'room_menu_items'
    room_id = Column(Integer, ForeignKey('event_rooms.id'), primary_key=True)
    food_item_id = Column(Integer, ForeignKey('food_items.id'), primary_key=True)


class Consumable(Base):
    __tablename__ = 'consumables'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    unit = Column(String(30), nullable=False)


class RecipeLine(Base):
    __tablename__ = 'recipe_lines'
    id = Column(Integer, primary_key=True)
    food_item_id = Column(Integer, ForeignKey('food_items.id'), nullable=False, index=True)
    consumable_id = Column(Integer, ForeignKey('consumables.id'), nullable=False)
    quantity = Column(Numeric(14, 3), nullable=False)
    __table_args__ = (UniqueConstraint('food_item_id', 'consumable_id'),)


class StockAdjustment(Base):
    __tablename__ = 'stock_adjustments'
    room_id = Column(Integer, ForeignKey('event_rooms.id'), nullable=True, index=True)
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('dinner_events.id'), nullable=False, index=True)
    consumable_id = Column(Integer, ForeignKey('consumables.id'), nullable=False)
    quantity = Column(Numeric(14, 3), nullable=False)
    reason = Column(String(200), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OrderConsumption(Base):
    __tablename__ = 'order_consumption'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)
    consumable_id = Column(Integer, ForeignKey('consumables.id'), nullable=False)
    name = Column(String(100), nullable=False)
    unit = Column(String(30), nullable=False)
    quantity = Column(Numeric(14, 3), nullable=False)


class OrderCounter(Base):
    __tablename__ = 'order_counter'
    id = Column(Integer, primary_key=True)
    value = Column(Integer, nullable=False, default=0)


class StationCheck(Base):
    __tablename__ = 'station_checks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_id = Column(Integer, ForeignKey('dinner_events.id'), nullable=False)
    checkout_key = Column(String(80), nullable=False)
    fingerprint = Column(String(64), nullable=False)
    station_number = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'checkout_key', name='uq_station_check'),)
