import asyncio

async def cancel_me():
    print('cancel_me(): before sleep')

    try:
        # Wait for 1 hour
        await asyncio.sleep(3600)
    except asyncio.CancelledError:
        print('cancel_me(): cancel sleep')
        raise
    finally:
        print('cancel_me(): after sleep')

async def main():
    # Create a "cancel_me" Task
    task = asyncio.create_task(cancel_me())

    # Wait for 1 second
    await asyncio.sleep(1)

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("main(): cancel_me is cancelled now")

asyncio.run(main())
# => 先快速过一遍，抄一遍代码，有问题的时候，知道这里面怎么完整表达异步编程遇到的大部分问题！然后复习再用出去
# cancel_me(): before sleep
# cancel_me(): cancel sleep
# cancel_me(): after sleep
# main(): cancel_me is cancelled now
#
