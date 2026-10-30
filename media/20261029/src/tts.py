import asyncio, io, json, sys
import edge_tts

VOICE = sys.argv[1] if len(sys.argv) > 1 else "zh-CN-YunxiNeural"
cues = json.load(io.open("cues.json", encoding="utf-8"))
sem = asyncio.Semaphore(4)

async def one(c):
    path = (sys.argv[2] if len(sys.argv) > 2 else "audio") + "/c%02d.mp3" % c["i"]
    async with sem:
        for attempt in range(3):
            try:
                comm = edge_tts.Communicate(c["text"].replace("\n", ""), VOICE, rate="+4%")
                await comm.save(path)
                print("ok", path, flush=True)
                return
            except Exception as e:
                print("retry", path, e, flush=True)
                await asyncio.sleep(1.5)
    print("FAIL", path, flush=True)

async def main():
    await asyncio.gather(*(one(c) for c in cues))

asyncio.run(main())
