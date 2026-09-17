"""Verifica herramientas OneNote pasando el token via estado de sesion.

Uso:
  uv run python scripts/verify_graph_tools.py --token "<ACCESS_TOKEN>" --search "proyecto"
"""

from __future__ import annotations

import argparse
from types import SimpleNamespace

from app.onenote_tools import get_page_content, list_pages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="Access token de Microsoft Graph")
    parser.add_argument(
        "--search",
        default="",
        help="Filtro opcional para titulo de pagina (list_pages)",
    )
    args = parser.parse_args()

    # Las tools solo necesitan un objeto con atributo .state.
    tool_context = SimpleNamespace(state={"ms_graph_token": args.token})

    pages_result = list_pages(search=args.search, tool_context=tool_context)
    print("list_pages =>", pages_result.get("status"))

    if pages_result.get("status") != "success":
        print(pages_result)
        return 1

    pages = pages_result.get("pages", [])
    print(f"Paginas encontradas: {len(pages)}")
    if not pages:
        print("No hay paginas para validar get_page_content.")
        return 0

    first = pages[0]
    print("Primera pagina:", first)

    content_result = get_page_content(page_id=first["id"], tool_context=tool_context)
    print("get_page_content =>", content_result.get("status"))
    if content_result.get("status") != "success":
        print(content_result)
        return 1

    text = content_result.get("text", "")
    print("Longitud texto:", len(text))
    print("Preview:")
    print(text[:500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
