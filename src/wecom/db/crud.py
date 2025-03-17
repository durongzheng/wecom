# from sqlalchemy.orm import Session
# from . import models, schemas

# def get_subscriber_by_email(db: Session, email: str):
#     return db.query(models.Subscriber).filter(models.Subscriber.contact_email == email).first()

# def create_subscriber(db: Session, subscriber: dict):
#     db_subscriber = models.Subscriber(**subscriber)
#     db.add(db_subscriber)
#     db.commit()
#     db.refresh(db_subscriber)
#     return db_subscriber