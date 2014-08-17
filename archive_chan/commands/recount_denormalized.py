from flask.ext import script
from ..database import db
from ..models import Thread, Post, Image

class Command(script.Command):
    """Recounts the denormalized data like number of posts or images
    in the thread. Can be used to fix the database.
    """

    def run(self):
        threads = db.session.query(
            Thread.id,
            Thread.replies,
            Thread.images,
            Thread.first_reply,
            Thread.last_reply,
            db.func.count(Post.id).label('correct_replies'),
            db.func.count(Image.id).label('correct_images'),
            db.func.min(Post.time).label('correct_first_reply'),
            db.func.max(Post.time).label('correct_last_reply'),
        ).join(Post).outerjoin(Image).group_by(Thread.id).all()

        total = 0
        updated = 0

        for thread in threads:
            if (thread.correct_first_reply != thread.first_reply
                or thread.correct_last_reply != thread.last_reply
                or thread.correct_replies != thread.replies
                or thread.correct_images != thread.images):
                db.session.query(Thread).filter(Thread.id==thread.id).update({
                    'first_reply': thread.correct_first_reply,
                    'last_reply': thread.correct_last_reply,
                    'replies': thread.correct_replies,
                    'images': thread.correct_images,

                })
                updated += 1
            total += 1
        db.session.commit()

        print('Total: %s Updated: %s' % (total, updated))
