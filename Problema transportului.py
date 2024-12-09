import zipfile  # Permite lucrul cu arhive ZIP
from scipy.optimize import linprog  # Rezolvă probleme de programare liniară
import numpy as np  # Lucru cu matrici și operații numerice
import time  # Măsurarea timpului de execuție
import pandas as pd  # Manipularea datelor și generarea fișierelor Excel
import os  # Gestionarea fișierelor și directoarelor
import shutil  # Gestionarea operațiilor de arhivare și copiere


def extract_instance_data(file):

    lines = file.readlines()  # Citește toate liniile din fișierul dat
    instance_name = ""  # Numele instanței
    d = 0  # Numărul de depozite
    r = 0  # Numărul de magazine
    SCj = []  # Capacitățile depozitelor
    Dk = []  # Cererea magazinelor
    Cjk = []  # Costurile de transport

    i = 0
    while i < len(lines):  # Iterează prin fiecare linie din fișier
        line = lines[i].decode('utf-8').strip()  # Decodează și elimină spațiile
        if line.startswith("instance_name"):  # Verifică dacă linia definește numele instanței
            instance_name = line.split('=')[1].strip().strip('";')
        elif line.startswith("d ="):  # Definirea numărului de depozite
            d = int(line.split('=')[1].strip().strip(';'))
        elif line.startswith("r ="):  # Definirea numărului de magazine
            r = int(line.split('=')[1].strip().strip(';'))
        elif line.startswith("SCj ="):  # Citirea capacităților depozitelor
            SCj = list(map(int, line.split('=')[1].strip().strip('[];').split()))
        elif line.startswith("Dk ="):  # Citirea cererii magazinelor
            Dk = list(map(int, line.split('=')[1].strip().strip('[];').split()))
        elif line.startswith("Cjk ="):  # Citirea costurilor de transport
            costs = []
            while not line.endswith("];"):  # Continuă până se termină blocul de costuri
                costs.extend([x for x in line.replace('[', '').replace(']', '').replace(';', '').split() if x.isdigit()])
                i += 1
                line = lines[i].decode('utf-8').strip()
            costs.extend([x for x in line.replace('[', '').replace(']', '').replace(';', '').split() if x.isdigit()])
            Cjk = [list(map(int, costs[i:i + r])) for i in range(0, len(costs), r)]  # Creează matricea Cjk

            if len(Cjk) != d or any(len(row) != r for row in Cjk):  # Validare dimensiuni
                raise ValueError(
                    f"Dimensiunea lui Cjk este incorectă: {len(Cjk)} x {len(Cjk[0])} (trebuie să fie {d} x {r})")

        i += 1

    return instance_name, d, r, SCj, Dk, Cjk  # Returnează datele instanței


def optimize_transportation(SCj, Dk, Cjk):
    """
    Rezolvă problema de transport folosind programarea liniară.
    """
    d = len(SCj)  # Numărul de depozite
    r = len(Dk)  # Numărul de magazine

    c = np.array(Cjk).flatten()  # Aplatizează matricea Cjk într-un vector

    A_ub = np.zeros((d, d * r))  # Matricea pentru constrângerile de capacitate
    for i in range(d):
        A_ub[i, i * r:(i + 1) * r] = 1  # Fiecare depozit are constrângeri individuale

    b_ub = SCj  # Vectorul de capacități

    A_eq = np.zeros((r, d * r))  # Matricea pentru constrângerile de cerere
    for j in range(r):
        A_eq[j, j::r] = 1  # Fiecare magazin primește exact cererea sa
    b_eq = Dk  # Vectorul cererii magazinelor

    bounds = [(0, None) for _ in range(d * r)]  # Limitele variabilelor (>= 0)

    start_time = time.time()  # Începe măsurarea timpului
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')  # Rezolvă problema
    end_time = time.time()  # Termină măsurarea timpului

    is_solved = result.success  # Verifică dacă problema a fost rezolvată
    optimal_cost = result.fun if is_solved else None  # Costul optim
    num_iterations = result.nit if is_solved else None  # Numărul de iterații
    run_time = end_time - start_time  # Timpul de execuție

    # Restructurăm soluția într-o matrice (Xjk)
    Xjk = None
    if is_solved:
        Xjk = np.array(result.x).reshape(d, r)  # Transformă vectorul soluției într-o matrice

    return optimal_cost, num_iterations, run_time, is_solved, Xjk  # Returnează rezultatele


def save_all_results(instances_results, output_file):
    """
    Salvează rezultatele tuturor instanțelor procesate într-un fișier Excel compact.
    """
    df = pd.DataFrame(instances_results, columns=['Instance', 'Optimal Cost', 'Iterations', 'Run Time (s)', 'Solved'])  # Creează un DataFrame
    df.to_excel(output_file, index=False)  # Salvează rezultatele într-un fișier Excel


def save_instance_results(instance_name, optimal_cost, num_iterations, run_time, is_solved, Xjk, output_folder):
    """
    Salvează rezultatele unei singure instanțe într-un fișier Excel separat.
    """
    df = pd.DataFrame([[instance_name, optimal_cost, num_iterations, run_time, is_solved]],
                      columns=['Instance', 'Optimal Cost', 'Iterations', 'Run Time (s)', 'Solved'])  # Creează un DataFrame pentru rezultate individuale
    output_file = f"{output_folder}/{instance_name}_solution.xlsx"  # Definește numele fișierului

    # Salvăm Xjk într-o foaie separată
    with pd.ExcelWriter(output_file) as writer:
        df.to_excel(writer, index=False, sheet_name="Summary")  # Salvează datele principale
        if Xjk is not None:
            pd.DataFrame(Xjk).to_excel(writer, index=False, header=False, sheet_name="Xjk")  # Salvează matricea Xjk


def process_transport_zip(zip_path, output_file):
    """
    Procesează toate instanțele dintr-un fișier ZIP, le rezolvă și salvează rezultatele.
    """
    instances_results = []  # Listă pentru toate rezultatele
    output_folder = "Individual_Solutions"  # Folderul unde se salvează fișierele individuale
    os.makedirs(output_folder, exist_ok=True)  # Creează folderul dacă nu există

    with zipfile.ZipFile(zip_path, 'r') as archive:  # Deschide arhiva ZIP
        for filename in archive.namelist():  # Iterează prin toate fișierele din arhivă
            if filename.endswith('.dat'):  # Procesăm doar fișierele `.dat`
                with archive.open(filename) as file:
                    instance_name, d, r, SCj, Dk, Cjk = extract_instance_data(file)  # Extrage datele instanței

                    optimal_cost, num_iterations, run_time, is_solved, Xjk = optimize_transportation(SCj, Dk, Cjk)  # Rezolvă problema

                    instances_results.append([
                        instance_name,
                        optimal_cost,
                        num_iterations,
                        run_time,
                        is_solved
                    ])  # Adaugă rezultatul la lista generală

                    save_instance_results(instance_name, optimal_cost, num_iterations, run_time, is_solved, Xjk, output_folder)  # Salvează rezultatul individual

    save_all_results(instances_results, output_file)  # Salvează toate rezultatele într-un fișier global

    shutil.make_archive("Lab_simple_solved_1-3", 'zip', output_folder)  # Creează o arhivă ZIP cu toate fișierele individuale


zip_path = 'Lab_simple_instances.zip'  # Calea către arhiva zip
output_file = 'Lab_simple_solved_results.xlsx'  # Calea către fișierul global de rezultate
process_transport_zip(zip_path, output_file)  # Procesează toate instanțele
