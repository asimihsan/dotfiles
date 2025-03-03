import argparse
import asyncio
import json

from olmocr.pipeline import build_page_query, PageResult
from olmocr.prompts import PageResponse
from openai import OpenAI
from pypdf import PdfReader


async def process_page(client, filename, page_num):
    query = await build_page_query(filename,
                                   page=page_num,
                                   target_longest_image_dim=1024,
                                   target_anchor_text_len=6000)
    query['model'] = 'allenai_olmocr-7b-0225-preview'
    response = client.chat.completions.create(**query)
    model_obj = json.loads(response.choices[0].message.content)
    page_response = PageResponse(**model_obj)

    return PageResult(
        filename,
        page_num,
        page_response,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        is_fallback=False,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process PDF files.")
    parser.add_argument(
        "filename", type=str, help="Path to the PDF file to process."
    )
    return parser.parse_args()

async def main():
    client = OpenAI(base_url="http://192.168.1.74:1234/v1", api_key="lm-studio", timeout=300)
    args = parse_args()
    filename = args.filename

    reader = PdfReader(filename)
    num_pages = reader.get_num_pages()

    for page_num in range(1, num_pages + 1):
        result = await process_page(client, filename, page_num)
        print(result.response.natural_text)

if __name__ == "__main__":
    asyncio.run(main())
