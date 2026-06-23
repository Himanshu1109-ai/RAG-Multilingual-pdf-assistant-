css = '''
<style>
body {
    background-color: #ffffff;
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}

.chat-message {
    background: #f1f2f6;
    border-radius: 1rem;
    margin: 0.75rem 0;
    padding: 1rem;
    display: flex;
    align-items: flex-start;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.chat-message.user {
    background-color: #e0f7fa;
}

.chat-message.bot {
    background-color: #e8eaf6;
}

.chat-message .avatar {
    width: 40px;
    height: 40px;
    margin-right: 1rem;
}

.chat-message .avatar img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #ccc;
}

.chat-message .message {
    flex: 1;
    color: #333;
    font-size: 1rem;
    line-height: 1.5;
}
</style>
'''


bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://cdn-icons-png.flaticon.com/128/773/773330.png">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''


user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://cdn-icons-png.flaticon.com/128/6997/6997674.png">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''
