"""Prueba remota del Agent Engine inyectando token de Graph en estado de sesion.

Uso:
  uv run python scripts/smoke_remote_with_graph_token.py \
    --project gcp1-prj-sv-dev-agentmind-01 \
    --location europe-west1 \
    --engine projects/241752938089/locations/europe-west1/reasoningEngines/6158276666243153920 \
    --token "<GRAPH_ACCESS_TOKEN>"
"""

from __future__ import annotations

import argparse

import vertexai
from vertexai import agent_engines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--location", default="europe-west1")
    parser.add_argument("--engine", required=True, help="Resource name del Reasoning Engine")
    parser.add_argument("--token", required=True, help="Access token delegado de Microsoft Graph")
    parser.add_argument("--user-id", default="onenote-smoke-user")
    args = parser.parse_args()

    vertexai.init(project=args.project, location=args.location)
    remote_app = agent_engines.get(args.engine)

    # Inyecta token de Graph en el estado de sesion.
    session = remote_app.create_session(
        user_id=args.user_id,
        state={"ms_graph_token": args.token},
    )
    session_id = session["id"]
    print(f"session_id={session_id}")

    prompt = (
        "Primero usa list_pages para encontrar paginas recientes. "
        "Despues usa get_page_content sobre la primera pagina y resume su contenido en 3 lineas, "
        "citando el titulo de la pagina."
    )

    events = list(
        remote_app.stream_query(
            user_id=args.user_id,
            session_id=session_id,
            message=prompt,
        )
    )

    print(f"events={len(events)}")
    if events:
        print(events[-1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
