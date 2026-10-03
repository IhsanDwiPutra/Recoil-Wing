# /// script
# dependencies = [
#     "pygame-ce",
# ]
# ///
"""
Main entry point for Recoil Wing.
Supports both native desktop and Pygbag (Android / Web / PWA).
"""
import asyncio
import pygame
from src.game import Game


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
