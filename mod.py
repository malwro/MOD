from docplex.mp.model import Model
import docplex.mp.conflict_refiner as cr
import argparse as ap
import numpy as np
import sys

# stała dodatnia do identyfikacji wyrażeń o dodatnich wartościach [1]
D =1000


def create_parser():
    parser = ap.ArgumentParser()

    # nr indeksu
    parser.add_argument('-i', type=int, required=True)
    # rozmiar zadania
    parser.add_argument('-n', type=int, required=True)
    # włączanie preprocessingu (domyślnie: brak)
    parser.add_argument('-p', default=False, action=ap.BooleanOptionalAction)

    return parser.parse_args()


def generate_params(n: int):
    # s_i - koszt uruchomienia produkcji wyrobu i [jednostka zysku/kosztu]
    s = np.random.uniform(low=0, high=10, size=n)
    # e_i - wstępne zużycie surowca na produkcję wyrobu i [jednostka zużycia]
    e = np.random.uniform(low=0, high=10, size=n)

    # c_i - jednostkowy zysk z produkcji wyrobu i [jednostka zysku/kosztu]
    c = np.random.uniform(low=0, high=100, size=n)
    # p_i - jednostkowe zużycie surowca na produkcję wyrobu i [jednostka zużycia]
    p = np.random.uniform(low=0, high=100, size=n)

    # Q - całkowita ilość dostępnego materiału [jednostka zużycia]
    Q = np.random.uniform(low=0, high=sum(e + p))

    # M_i - maksymalna wielkość produkcji wyrobu i [1]
    M = [1]*n
    
    return s, e, c, p, Q, M


if __name__ == '__main__':
    args = create_parser()

    rnd = np.random
    seed_val = args.i

    for k in range(1,6):
        seed_val += args.n + k
        rnd.seed(seed_val)

        name = f"n{args.n}_k{k}.txt"
        sys.stdout = open(name, 'w')

        s, e, c, p, Q, M = generate_params(args.n)
        print(f"s_i - koszt uruchomienia produkcji wyrobu i [jednostka zysku/kosztu]:\n{s}")
        print(f"e_i - wstępne zużycie surowca na produkcję wyrobu i [jednostka zużycia]:\n{e}")
        print(f"c_i - jednostkowy zysk z produkcji wyrobu i [jednostka zysku/kosztu]:\n{c}")
        print(f"p_i - jednostkowe zużycie surowca na produkcję wyrobu i [jednostka zużycia]:\n{p}")

        model = Model(log_output=True)

        if (args.p == False):
            model.parameters.preprocessing.presolve = False

        # ZMIENNE
        # wielkość produkcji wyrobu i, zmienna całkowita
        x = model.integer_var_list(args.n, name="x")
        # zmienna binarna (1, jeżeli wyrób i jest produkowany, 0, jeżeli nie)
        y = model.binary_var_list(args.n, name="y")

        # OGRANICZENIA
        # ograniczenie na nieujemność wielkości produkcji wyrobu i
        model.add_constraints((x[i] >= 0 for i in range(args.n)), names="ogr1")
        # ograniczenie na maksymalną wielkość produkcji wyrobu i
        model.add_constraints((x[i] <= M[i] for i in range(args.n)), names="ogr2")
        # ograniczenie związane z identyfikacją wyrażenia o dodatniej wartości
        # (dot. uruchomienia produkcji wyrobu i)
        model.add_constraints((x[i] <= D*y[i] for i in range(args.n)), names="ogr3")
        # ograniczenie związane z całkowitą ilością dostępnego surowca
        model.add_constraint((sum((p[i]*x[i]+e[i]*y[i]) for i in range(args.n)) <= Q), ctname="ogr4")

        # FUNKCJA CELU
        obj_fun = sum(c[i]*x[i]-s[i]*y[i] for i in range(args.n))
        model.set_objective('max', obj_fun)

        model.print_information()

        model.solve()
        solve_status = model.get_solve_status()
        if solve_status.name == 'INFEASIBLE_SOLUTION':
            cref = cr.ConflictRefiner()
            cref.refine_conflict(model, display=True)

        model.print_solution()
        
        print(f"Liczba sondowanych wierzchołków: {model.solve_details.nb_nodes_processed}")
        print(f"Czas [s]: {model.solve_details.time}")

        sys.stdout.close()