import os
import sys
import random
import django
from django.db import IntegrityError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatterchums.settings')
django.setup()

# Import Django models (must be after django.setup())
from django.utils import timezone
from django.contrib.auth.models import User, Group

from forums.models import Tag, Forum, Topic, Comment, Complaint


def populate_tags():
    tags = [
        'Technology', 'Gaming', 'Rom-Coms', 'Sports', 'Science',
        'Art', 'Music', 'Movies', 'Literature', 'Food', 'Travel', 'Fashion',
        'Health', 'Fitness', 'Politics', 'Radiohead', 'Finance',
        'TV Shows', 'Studio Ghibli', 'Comics', 'Podcasts', 'Celebrities',
        'Rock', 'Pop', 'Hip-Hop', 'Jazz', 'Classical', 'Electronic',
        'Lord of the Rings', 'Harry Potter', 'History', 'Philosophy', 'R&B',
        'Harry Potter', 'Breaking Bad', 'Martin Scorsese', 'House', 'Nintendo',
        'Horror', 'Disney', 'K-Pop', 'The Smiths', 'Fantasy', 'Stephen King',
        'Taylor Swift', 'Weightlifting'
    ]

    created_count = 0
    existing_count = 0

    for tag_name in tags:
        tag, created = Tag.objects.get_or_create(name=tag_name)
        if created:
            created_count += 1
            print(f"Created tag: {tag_name}")
        else:
            existing_count += 1

    print(f"\nTag population summary:")
    print(f"Created: {created_count}")
    print(f"Already existed: {existing_count}")
    print(f"Total tags: {len(tags)}")

    return Tag.objects.all()


def create_users():
    # Ensure groups exist
    admin_group, _ = Group.objects.get_or_create(name='administrator')
    moderator_group, _ = Group.objects.get_or_create(name='moderator')

    users_data = [
        {'username': 'admin1', 'email': 'admin1@gmail.com', 'password': '!apassword10', 'roles': ['admin']},
        {'username': 'moderator1', 'email': 'moderator1@gmail.com', 'password': '£apassword20', 'roles': ['moderator']},
        {'username': 'john', 'email': 'john@yahoo.com', 'password': '!apassword1', 'roles': ['admin']},
        {'username': 'jane', 'email': 'jane@gmail.com', 'password': '£apassword2', 'roles': ['moderator']},
        {'username': 'alex', 'email': 'alex@gmail.com', 'password': '$apassword3', 'roles': []},
        {'username': 'sam', 'email': 'sam@design.com', 'password': '!apassword4', 'roles': ['moderator']},
        {'username': 'taylor', 'email': 'taylor@gmail.com', 'password': '£apassword5', 'roles': []},
        {'username': 'jordan', 'email': 'jordan@gmail.com', 'password': '$apassword6', 'roles': []},
        {'username': 'robin', 'email': 'robin@gmail.com', 'password': '!apassword7', 'roles': []},
        {'username': 'casey', 'email': 'casey@gmail.com', 'password': '$apassword8', 'roles': []},
        {'username': 'morgan', 'email': 'morgan@swiftie.com', 'password': '!apassword9', 'roles': []},
        {'username': 'riley', 'email': 'riley@horror.net', 'password': '£apassword10', 'roles': []},
        {'username': 'jamie', 'email': 'jamie@ghibli.jp', 'password': '$apassword11', 'roles': ['admin']},
        {'username': 'quinn', 'email': 'quinn@radiohead.fan', 'password': '!apassword12', 'roles': []},
        {'username': 'parker', 'email': 'parker@gmail.com', 'password': '£apassword13', 'roles': []},
    ]

    created_users = []
    created_count = 0
    existing_count = 0
    all_tags = list(Tag.objects.all())

    for user_data in users_data:
        try:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                email=user_data['email'],
                defaults={'is_active': True}
            )

            if created:
                user.set_password(user_data['password'])
                user.save()
                created_count += 1
                print(f"Created user: {user.username}")
            else:
                existing_count += 1

            # Assign to groups
            roles = user_data.get('roles', [])
            if 'admin' in roles:
                user.groups.add(admin_group)
            if 'moderator' in roles:
                user.groups.add(moderator_group)

            # Призначення випадкових тегів-інтересів
            profile = user.userprofile
            if len(all_tags) >= 4:  # на випадок, якщо ще не заповнили
                random_tags = random.sample(all_tags, random.randint(3, 4))
                profile.interests.set(random_tags)
                profile.save()

            created_users.append(user)

        except IntegrityError:
            print(f"Error creating user {user_data['username']}, skipping...")

    print(f"\nUser creation summary:")
    print(f"Created: {created_count}")
    print(f"Already existed: {existing_count}")
    print(f"Total users: {len(created_users)}")

    return created_users


def create_forums(users, tags):
    forums_data = [
        {
            'title': 'Tech Space',
            'description': 'For the latest technology trends and innovations.',
            'tag_names': ['Technology', 'Science', 'Education', 'Electronic'],
        },
        {
            'title': 'Game Zone',
            'description': 'Discuss, get tips, and find new games.',
            'tag_names': ['Gaming', 'Entertainment', 'Technology', 'Nintendo', 'Fantasy'],
        },
        {
            'title': 'Music Lovers',
            'description': 'For those who appreciate all genres of music.',
            'tag_names': ['Music', 'Rock', 'Pop', 'Jazz', 'Classical', 'Hip-Hop', 'R&B', 'Radiohead', 'K-Pop', 'The Smiths', 'Taylor Swift'],
        },
        {
            'title': 'Book Club',
            'description': 'Discuss your favorite books and discover new reads.',
            'tag_names': ['Literature', 'Education', 'Entertainment', 'Harry Potter', 'Lord of the Rings', 'Fantasy', 'Stephen King'],
        },
        {
            'title': 'Globetrotting',
            'description': 'Share your travel stories and get inspiration for your next trip.',
            'tag_names': ['Travel', 'Food', 'Photography'],
        },
        {
            'title': 'One Stop Fitness',
            'description': 'Support and motivation for your fitness goals.',
            'tag_names': ['Fitness', 'Health', 'Sports', 'Weightlifting'],
        },
        {
            'title': 'Cinema Forum',
            'description': 'Discussions about movies, directors, and actors.',
            'tag_names': ['Movies', 'Entertainment', 'Celebrities', 'Studio Ghibli', 'Horror', 'Disney', 'Martin Scorsese'],
        },
        {
            'title': 'Swifties',
            'description': 'Taylor Swift - music, concerts, theories, and eras.',
            'tag_names': ['Taylor Swift', 'Music', 'Pop', 'Celebrities'],
        },
        {
            'title': 'Horror Fanatics',
            'description': 'For fans of horror movies, books, and all things spooky.',
            'tag_names': ['Horror', 'Movies', 'Stephen King', 'Entertainment'],
        },
        {
            'title': 'Studio Ghibli',
            'description': 'Celebrating the magical world of Miyazaki and Studio Ghibli films.',
            'tag_names': ['Studio Ghibli', 'Movies', 'Animation', 'Art'],
        },
        {
            'title': 'TV Chat',
            'description': 'Analysis and discussions of popular and classic television series.',
            'tag_names': ['TV Shows', 'Entertainment', 'Breaking Bad', 'House'],
        },
    ]

    created_forums = []
    created_count = 0
    existing_count = 0

    # Get tag objects by name
    tag_dict = {tag.name: tag for tag in tags}

    for forum_data in forums_data:
        creator = random.choice(users)

        # Check if forum already exists
        existing_forum = Forum.objects.filter(title=forum_data['title']).first()

        if existing_forum:
            existing_count += 1
            created_forums.append(existing_forum)
            continue

        # Create new forum
        new_forum = Forum.objects.create(
            creator=creator,
            name=creator.username,
            title=forum_data['title'],
            description=forum_data['description'],
            date_posted=timezone.now()
        )

        # Add tags
        for tag_name in forum_data['tag_names']:
            if tag_name in tag_dict:
                new_forum.tags.add(tag_dict[tag_name])

        # Add creator as member
        new_forum.members.add(creator)

        # Add random members (between 2 and 6 additional members)
        potential_members = [u for u in users if u != creator]
        member_count = min(len(potential_members), random.randint(2, 6))
        random_members = random.sample(potential_members, member_count)

        for member in random_members:
            new_forum.members.add(member)

        created_count += 1
        created_forums.append(new_forum)
        print(f"Created forum: {new_forum.title}")

    print(f"\nForum creation summary:")
    print(f"Created: {created_count}")
    print(f"Already existed: {existing_count}")
    print(f"Total forums: {len(created_forums)}")

    return created_forums


def create_topics_and_comments(forums):
    sample_topics = [
        {
            'title': 'Welcome to our community!',
            'content': 'Hello everyone! Welcome to our forum. Feel free to introduce yourself and share your interests.',
        },
        {
            'title': 'Forum Rules',
            'content': 'Please review our community guidelines: Be respectful, no spam, and have fun!',
        },
        {
            'title': 'What brought you here?',
            'content': "I'm curious to know what brought everyone to this community. Share your story!",
        },
        {
            'title': 'Monthly Discussion Thread',
            'content': "This month's topic is all about your favorite experiences. Let's share and discuss!",
        },
        {
            'title': 'Looking for recommendations',
            'content': "I'm new to this area and looking for recommendations. What are your favorites?",
        },
        {
            'title': 'Upcoming Events',
            'content': "Let's compile a list of upcoming events related to our interests. Share anything you know about!",
        },
    ]

    sample_comments = [
        "Great post! I completely agree with your points.",
        "Thanks for sharing this information. It was very helpful.",
        "I had a similar experience and can relate to this.",
        "Interesting perspective. I hadn't thought about it that way.",
        "I have a question about your post. Can you clarify?",
        "This is exactly what I needed to know!",
        "I disagree with some points, but appreciate the discussion.",
        "Has anyone else experienced this issue?",
        "I'm new here, but this seems like a great community.",
        "Looking forward to more posts like this one!",
    ]

    topics_created = 0
    comments_created = 0

    for forum in forums:
        # Create 2-4 topics per forum
        topic_count = random.randint(2, 4)
        forum_topics = random.sample(sample_topics, min(topic_count, len(sample_topics)))

        for topic_data in forum_topics:
            # Get members of the forum
            members = forum.members.all()
            if not members:
                author = forum.creator
            else:
                author = random.choice(list(members))

            # Create topic
            topic = Topic.objects.create(
                forum=forum,
                author=author,
                title=topic_data['title'],
                content=topic_data['content'],
                views=random.randint(5, 50)
            )
            topics_created += 1

            # Create 2-6 comments per topic
            comment_count = random.randint(2, 6)

            for _ in range(comment_count):
                members = forum.members.all()
                if not members:
                    comment_author = forum.creator
                else:
                    comment_author = random.choice(list(members))
                comment_text = random.choice(sample_comments)

                Comment.objects.create(
                    topic=topic,
                    author=comment_author,
                    content=comment_text
                )
                comments_created += 1

    print(f"\nContent creation summary:")
    print(f"Topics created: {topics_created}")
    print(f"Comments created: {comments_created}")

def create_complaints():
    complaint_types = ['hate_speech', 'spam', 'offensive', 'harassment', 'other']
    users = list(User.objects.all())
    forums = list(Forum.objects.all())
    topics = list(Topic.objects.all())
    comments = list(Comment.objects.all())

    created_count = 0

    for _ in range(5):
        author = random.choice(users)

        target_type = random.choice(['forum', 'topic', 'comment'])
        complaint_type = random.choice(complaint_types)
        complaint_text = f"Random complaint about {target_type} - {complaint_type}"

        complaint_kwargs = {
            'author': author,
            'complaint_type': complaint_type,
            'complaint_text': complaint_text,
        }

        if target_type == 'forum' and forums:
            complaint_kwargs['forum_target'] = random.choice(forums)
        elif target_type == 'topic' and topics:
            complaint_kwargs['topic_target'] = random.choice(topics)
        elif target_type == 'comment' and comments:
            complaint_kwargs['comment_target'] = random.choice(comments)
        else:
            continue

        try:
            complaint = Complaint.objects.create(**complaint_kwargs)
            print(f"Created complaint: {complaint}")
            created_count += 1
        except Exception as e:
            print(f"Error creating complaint: {e}")

    print(f"\nComplaint creation summary:")
    print(f"Created: {created_count}")

def populate():
    tags = populate_tags()
    users = create_users()
    forums = create_forums(users, tags)
    create_topics_and_comments(forums)
    create_complaints()

    print("\nPopulation completed successfully.")

if __name__ == '__main__':
    populate()