import glob
import pandas as pd
import numpy as np
import asyncio
import sys
from sklearn.cluster import KMeans
from openai import AsyncOpenAI

# windows or not?
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# read API key
with open("key.txt", "r", encoding="utf-8") as f:
    OPENAI_API_KEY = f.read().strip()

# async helper
async def async_get_embeddings(client, texts, model):
    response = await client.embeddings.create(
        input=texts,
        model=model
    )
    return [item.embedding for item in response.data]

# clustering
def create_clusters(embeddings, n_clusters):
    embeddings_np = np.array(embeddings)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    return kmeans.fit_predict(embeddings_np)

async def main():

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    file_type = "research articles"
    input_files = glob.glob(f"./01.3_Input_Files_CSV/{file_type}/*.csv")

    model = "text-embedding-3-small"

    done_files = glob.glob(
        f"./02_Parsed_Input_Files_to_Sources/{file_type}/*.parquet"
    )
    done_files = [
        #i.split("/")[-1].split("_clustered.")[0]
        i.split("\\")[-1].split("_clustered.")[0] # for windows
        for i in done_files
    ]

    not_done_files = [
        i for i in input_files
        if i.split("\\")[-1].split(".csv")[0] not in done_files # for windows
        #if i.split("/")[-1].split(".csv")[0] not in done_files
    ]

    for i in not_done_files:
        print(f"Processing: {i}")

        df = pd.read_csv(i, index_col=0)

        # Arxiv logic
        df["text_only"] = df.apply(
            lambda row: str(row["content"])
            if not isinstance(row["text_only"], str)
            else str(row["text_only"]),
            axis=1
        )

        df["text_len"] = df["text_only"].apply(len)

        df = df[df["text_len"] > 50].copy()
        df = df[df["text_len"] < 150_000].copy()

        texts = df["text_only"].astype(str).tolist()

        # chunked embedding
        embeddings = []
        chunk_size = 100
        chunks = [
            texts[i:i + chunk_size]
            for i in range(0, len(texts), chunk_size)
        ]

        for chunk in chunks:
            try:
                emb = await async_get_embeddings(client, chunk, model)
            except Exception as e:
                print("Embedding failed, using NA fallback:", e)
                emb = await async_get_embeddings(
                    client, ["NA"] * len(chunk), model
                )
            embeddings.extend(emb)

        # clustering
        n_clusters = max(1, len(df) // 15)
        df["cluster"] = create_clusters(embeddings, n_clusters)
        df[f"embeddings_{model}"] = embeddings

        file_name = i.split("/")[-1].replace(".csv", "").split("\\")[-1] # last condition for windows
        df.to_parquet(
            f"./02_Parsed_Input_Files_to_Sources/"
            f"{file_type}/{file_name}_clustered.parquet"
        )

# run
if __name__ == "__main__":
    asyncio.run(main())
