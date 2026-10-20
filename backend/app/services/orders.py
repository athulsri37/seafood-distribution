from app.models.order import OrderStatus

# Orders move forward one step at a time and can be cancelled until they ship.
# DELIVERED and CANCELLED are final: a cancelled order is never reopened, because
# its stock has already been returned.
ALLOWED_TRANSITIONS: dict[OrderStatus, tuple[OrderStatus, ...]] = {
    OrderStatus.PENDING: (OrderStatus.CONFIRMED, OrderStatus.CANCELLED),
    OrderStatus.CONFIRMED: (OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED),
    OrderStatus.IN_TRANSIT: (OrderStatus.DELIVERED,),
    OrderStatus.DELIVERED: (),
    OrderStatus.CANCELLED: (),
}


def next_statuses(status: OrderStatus) -> tuple[OrderStatus, ...]:
    return ALLOWED_TRANSITIONS[status]


def transition_error(order_id: int, current: OrderStatus, requested: OrderStatus) -> str:
    """Explain why `current` can't change to `requested`, in words a user can act on."""
    allowed = next_statuses(current)
    if not allowed:
        return f"Order #{order_id} is {current.value}, which is final. Its status can't change."
    options = " or ".join(s.value for s in allowed)
    return f"Order #{order_id} can't go from {current.value} to {requested.value}. Next it can be {options}."
