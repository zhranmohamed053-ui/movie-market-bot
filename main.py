# ---------------------------------------------------------------------------
def main():
    acquire_lock()
    try:
        init_db()

        # Start Flask in a background daemon thread
        flask_thread = threading.Thread(target=start_flask, daemon=True)
        flask_thread.start()
        logger.info("Flask keep-alive server started on port 5000")

        logger.info("Starting bot — channel_id=%s", CHANNEL_ID)

        app = Application.builder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start",   start_command))
        app.add_handler(CommandHandler("count",   count_command))
        app.add_handler(CommandHandler("recent",  recent_command))
        app.add_handler(CommandHandler("search",  search_command))
        app.add_handler(CommandHandler("pending", pending_command))

        # Live channel posts
        app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post_handler))

        # Admin replies to 'movie not found' notifications (must come before text_search)
        app.add_handler(MessageHandler(
            filters.Chat(ADMIN_ID) & filters.TEXT & filters.REPLY & ~filters.COMMAND,
            admin_reply_handler,
        ))

        # Backfill: forwards from the channel sent to private chat
        app.add_handler(MessageHandler(
            filters.ChatType.PRIVATE & filters.FORWARDED,
            backfill_handler,
        ))

        # Plain text in private chat → instant search (must be last)
        app.add_handler(MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND & ~filters.FORWARDED,
            text_search_handler,
        ))

        app.run_polling(
            allowed_updates=["channel_post", "message"],
            drop_pending_updates=True,
        )
    finally:
        release_lock()


if name == "__main__":
    main()
