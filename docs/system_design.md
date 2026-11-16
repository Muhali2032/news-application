
# News Application – System Design

## 1. Introduction

This document presents the system design for the News Application. It includes a use-case diagram, an article-approval sequence diagram and a class diagram.

The diagrams represent the application's three user roles, its main workflows and the relationships between its database models.

## 2. Use-Case Diagram

The use-case diagram shows the main activities available to Readers, Journalists and Editors.

```mermaid
flowchart LR
    Reader([Reader])
    Journalist([Journalist])
    Editor([Editor])

    subgraph NewsApplication["News Application"]
        ViewArticles([View approved articles])
        ViewNewsletters([View newsletters])
        ViewSubscriptions([View subscribed articles])
        CreateArticle([Create article])
        EditOwnArticle([Edit own article])
        DeleteOwnArticle([Delete own article])
        CreateNewsletter([Create newsletter])
        ManageOwnNewsletter([Manage own newsletter])
        ReviewArticles([View pending articles])
        ApproveArticle([Approve article])
        ManageArticles([Edit or delete articles])
        ManageNewsletters([Manage newsletters])
    end

    Reader --> ViewArticles
    Reader --> ViewNewsletters
    Journalist --> ViewNewsletters
    Editor --> ViewNewsletters
    Reader --> ViewSubscriptions

    Journalist --> ViewArticles
    Journalist --> CreateArticle
    Journalist --> EditOwnArticle
    Journalist --> DeleteOwnArticle
    Journalist --> CreateNewsletter
    Journalist --> ManageOwnNewsletter

    Editor --> ViewArticles
    Editor --> ReviewArticles
    Editor --> ApproveArticle
    Editor --> ManageArticles
    Editor --> CreateNewsletter
    Editor --> ManageNewsletters
```

## 3. Article Approval Sequence Diagram

This sequence diagram illustrates how an editor approves an article and how the application processes subscriber notifications and the webhook.
```mermaid
sequenceDiagram
    autonumber
    actor Editor
    participant API as Django API
    participant DB as MariaDB
    participant Email as Django Console Email Backend
    participant Webhook as Local Approved Article API

    Editor->>API: Request article approval
    API->>API: Check editor permissions

    alt User is not an editor
        API-->>Editor: 403 Forbidden
    else User is an editor
        API->>DB: Retrieve article

        alt Article does not exist
            DB-->>API: Article not found
            API-->>Editor: 404 Not Found
        else Article already approved
            DB-->>API: Article already approved
            API-->>Editor: 400 Bad Request
        else Article requires approval
            DB-->>API: Return article
            API->>DB: Set approved = True
            DB-->>API: Confirm saved article
            API->>DB: Find subscribed readers
            DB-->>API: Return subscriber details

            API->>Email: Send notification emails
            alt Email succeeds
                Email-->>API: Email sent
            else Email fails
                Email-->>API: Email error
                Note over API: Record email error
            end

            API->>Webhook: POST approved article details
            alt Webhook succeeds
                Webhook-->>API: HTTP success
            else Webhook fails
                Webhook-->>API: Webhook error
                Note over API: Record webhook error
            end

            Note over API,DB: Article remains approved
            API-->>Editor: Return approval result
        end
    end
```

 

## 4. Class Diagram

The class diagram shows the main models and their relationships.

```mermaid
classDiagram

    class User {
        +username: CharField
        +email: EmailField
        +role: CharField
        +publisher_subscriptions: ManyToManyField
        +journalist_subscriptions: ManyToManyField
    }

    class Publisher {
        +name: CharField
        +description: TextField
        +editors: ManyToManyField
        +journalists: ManyToManyField
    }

    class Article {
        +title: CharField
        +content: TextField
        +author: ForeignKey
        +publisher: ForeignKey (optional)
        +created_at: DateTimeField
        +approved: BooleanField
        +clean()
    }

    class Newsletter {
        +title: CharField
        +description: TextField
        +author: ForeignKey
        +articles: ManyToManyField
        +created_at: DateTimeField
        +clean()
    }

    User "1" --> "0..*" Article : authors
    Publisher "0..1" --> "0..*" Article : publishes
    User "0..*" --> "0..*" Publisher : subscribes to
    User "0..*" --> "0..*" User : subscribes to journalists
    Publisher "0..*" -- "0..*" User : editors
    Publisher "0..*" -- "0..*" User : journalists
    User "1" --> "0..*" Newsletter : creates
    Newsletter "0..*" -- "0..*" Article : contains


```

## 5. Design Explanation

### User roles

The application uses a custom Django user model with three roles: Reader, Editor and Journalist. Role-based permissions control which operations each user can perform.

### Article management

Journalists create articles. Articles are associated with a journalist and may optionally be linked to a publisher. Articles are initially unapproved and require editorial approval before appearing in the approved article listing.

### Subscriptions

Readers can subscribe to individual journalists and publishers. These relationships support the subscribed-articles API endpoint and subscriber notification processing.

### Newsletters

Journalists and Editors can create newsletters containing selected articles. The newsletter model uses a many-to-many relationship with articles because one newsletter can contain multiple articles.

### Database

MariaDB stores the application's users, publishers, articles and newsletters. Django ORM manages database relationships and migrations.

## 6. Conclusion

The design separates user responsibilities, content management and editorial approval. Django models represent the application's data, views and API endpoints handle application operations, and role-based permissions protect restricted functionality.

