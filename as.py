import aiohttp
import asyncio

async def main():

    async with aiohttp.ClientSession() as session:
        for url in [
            "https://staff.am/en/senior-qa-engineer-desktop-15",
            # ""
            "https://staff.am/en/senior-qa-engineer-desktop-15",
        ]:
            async with session.get(url) as response:

                print("Status:", response.status)
                print("Content-type:", response.headers['content-type'])

                html = await response.text()
                print("Body:", html[:15], "...")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
