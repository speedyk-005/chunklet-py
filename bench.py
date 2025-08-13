import timeit
from rich.console import Console
from rich.panel import Panel
from rich.status import Status

from chunklet import Chunklet

chunker = Chunklet(token_counter=len, use_cache=False)
console = Console()

# Sample texts
english_text = """  
Every time you do something, it leaves a trace in your brain. When you do the same thing multiple times, the trace becomes stronger. That's why everything you're used to doing, you do it more easily because it has a path already traced in your mind.  
When you learn new knowledge, your brain works hard to retain it. It's like building a bridge between old information and new information. As time passes, these bridges become more solid, and you can use your knowledge with more ease.  
In daily life, when you concentrate and take the time to understand something well, you improve your ability to remember it. That's why it's important to repeat and practice what you learn.  
While engaging in creative activities like drawing, music, or writing, your brain creates new paths and ideas that didn't exist before. This helps you develop your ability to solve problems and express yourself better.  
Keeping an open mind and always being ready to learn will allow you to grow every day. Every new experience and knowledge is a step on the path to becoming a more complete and productive person.  
""" * 25

catalan_text = """  
Cada vegada que fas alguna cosa, deixa una empremta al teu cervell. Quan fas la mateixa cosa diverses vegades, aquesta empremta es fa més forta. Per això tot allò que estàs acostumat a fer, ho fas més fàcilment, perquè ja té un camí traçat a la teva ment.  
Quan aprens coneixements nous, el teu cervell treballa intensament per retenir-los. És com construir un pont entre la informació antiga i la nova. Amb el temps, aquests ponts es tornen més sòlids i pots utilitzar el teu coneixement amb més facilitat.  
A la vida quotidiana, quan et concentres i dediques temps a entendre bé alguna cosa, millores la teva capacitat de recordar-la. Per això és important repetir i practicar el que aprens.  
Quan participes en activitats creatives com dibuixar, fer música o escriure, el teu cervell crea camins i idees noves que abans no existien. Això t’ajuda a desenvolupar la teva capacitat per resoldre problemes i expressar-te millor.  
Mantenir la ment oberta i estar sempre disposat a aprendre et permetrà créixer cada dia. Cada nova experiència i coneixement és un pas en el camí per convertir-te en una persona més completa i productiva.  
""" * 25

haitian_creole_text = """
Chak fwa ou fè yon bagay, sa lese yon tras nan sèvo ou. Lè ou fè menm bagay la plizyè fwa, tras la vin pi fò. Se poutèt sa tout bagay ou abitue fè, ou fè'l pi fasil paske bagay la gen chemen tou trase nan lespri ou.
Lè ou aprann yon nouvo konesans, sèvo ou travay di pou kenbe li. Se tankou w ap bati yon pon ant ansyen enfòmasyon ak nouvo enfòmasyon yo. Pandan tan pase, pon sa yo vin pi solid, e ou ka itilize konesans ou avèk plis fasilite.
Nan lavi chak jou, lè ou konsantre epi pran tan pou konprann yon bagay byen, ou amelyore kapasite ou pou sonje li. Se poutèt sa li enpòtan pou repete epi pratike sa w ap aprann.
Pandan w ap fè aktivite kreyatif tankou desen, mizik, oswa ekriti, sèvo ou kreye nouvo chemen ak ide ki pa t egziste avan. Sa ede w devlope kapasite ou pou rezoud pwoblèm ak eksprime tèt ou pi byen.
Kenbe yon lespri ouvè epi toujou pare pou aprann ap pèmèt ou grandi chak jou. Chak nouvo eksperyans ak konesans se yon etap sou wout la pou vin yon moun ki pi konplè ak pwodiktif.
""" * 25

BENCHMARK_ITERATIONS = 256
console = Console()


def run_benchmark(label: str, func, params: dict):
    """Runs a benchmark with rich output showing parameters and timing."""
    param_lines = "\n".join(f"{k}: {v}" for k, v in params.items())
    console.print(
        Panel.fit(
            f"[bold]Parameters:[/]\n{param_lines}",
            title=f"Benchmark Parameters - {label}",
            border_style="cyan",
        )
    )
    with Status(f"[bold blue]Chunklet[/] Running benchmark: {label}...", console=console) as status:
        time_taken = timeit.timeit(func, number=BENCHMARK_ITERATIONS)
        avg_time = time_taken / BENCHMARK_ITERATIONS
        status.update(f"[bold green]Completed[/] {label}, avg_time = {avg_time:.4f}s")
    console.print(f"{label}\n[yellow]Average time: {avg_time:.4f}s[/]\n")


def benchmark_chunk_modes():
    console.rule("[bold magenta]Benchmark: Chunk Modes")
    for mode in ["sentence", "token", "hybrid"]:
        label = f"Chunk mode: {mode}"
        params = {
            "Iterations": BENCHMARK_ITERATIONS,
            "Text length (chars)": len(english_text),
            "Mode": mode,
        }
        run_benchmark(label, lambda: chunker.chunk(english_text, mode=mode), params)


def benchmark_batching():
    console.rule("[bold magenta]Benchmark: Batch Chunking")
    batch_texts = [english_text, catalan_text, haitian_creole_text]
    n_texts = len(batch_texts)
    total_chars = sum(len(t) for t in batch_texts)

    label = "Batch chunking"
    params = {
        "Iterations": BENCHMARK_ITERATIONS,
        "Number of texts": n_texts,
        "Total text length (chars)": total_chars,
    }
    run_benchmark(label, lambda: chunker.batch_chunk(batch_texts), params)


if __name__ == "__main__":
    benchmark_chunk_modes()
    benchmark_batching()