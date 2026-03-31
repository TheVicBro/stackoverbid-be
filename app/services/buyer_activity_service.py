from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.daos import bid_dao, item_dao, order_dao
from app.schemas import schemas


def _end_sort_key(r: schemas.MyBidItemRow) -> datetime:
    if r.end_time is None:
        return datetime.max.replace(tzinfo=timezone.utc)
    if r.end_time.tzinfo is None:
        return r.end_time.replace(tzinfo=timezone.utc)
    return r.end_time.astimezone(timezone.utc)


def get_my_buyer_dashboard(db: Session, user_id: int) -> schemas.MyBuyerDashboard:
    bid_rows = bid_dao.list_max_bid_per_item_for_user(db, user_id)
    my_max_by_item = {iid: amt for iid, amt in bid_rows}
    item_ids = list(my_max_by_item.keys())
    items = item_dao.get_items_by_ids(db, item_ids)
    by_id = {i.id: i for i in items}

    active_bids: list[schemas.MyBidItemRow] = []
    won_awaiting: list[schemas.MyBidItemRow] = []
    other: list[schemas.MyBidItemRow] = []

    def row_for(item) -> schemas.MyBidItemRow:
        return schemas.MyBidItemRow(
            item_id=item.id,
            title=item.title,
            status=item.status,
            current_price=item.current_price,
            my_highest_bid=my_max_by_item[item.id],
            end_time=item.end_time,
        )

    for iid in item_ids:
        item = by_id.get(iid)
        if not item:
            continue
        r = row_for(item)
        if item.status == "active":
            active_bids.append(r)
        elif item.status == "closed" and item.highest_bidder_id == user_id:
            won_awaiting.append(r)
        elif item.status == "paid" and item.highest_bidder_id == user_id:
            continue
        else:
            other.append(r)

    active_bids.sort(key=_end_sort_key)
    won_awaiting.sort(key=lambda x: x.title.lower())
    other.sort(key=lambda x: x.title.lower())

    orders = order_dao.list_orders_for_user(db, user_id)
    purchases: list[schemas.MyPurchaseRow] = []
    for o in orders:
        it = item_dao.get_item(db, o.item_id)
        purchases.append(
            schemas.MyPurchaseRow(
                order_id=o.id,
                item_id=o.item_id,
                item_title=it.title if it else "",
                amount_paid=o.amount_paid,
                paid_at=o.created_at,
            )
        )

    return schemas.MyBuyerDashboard(
        active_bids=active_bids,
        won_awaiting_payment=won_awaiting,
        other_auctions_i_bid_on=other,
        purchases=purchases,
    )
