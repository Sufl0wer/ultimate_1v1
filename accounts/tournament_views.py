from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from accounts.models import Discipline, Tournament, TournamentDisciplineResult, TournamentPlayer
from services.speedrun.client import SpeedrunClient


def _get_membership(tournament: Tournament, user) -> TournamentPlayer | None:
    return tournament.players.filter(user=user).first()


def _discipline_rows(tournament: Tournament) -> list[dict]:
    winners = {
        result.discipline_id: result.winner
        for result in tournament.discipline_results.select_related("winner")
    }
    players = list(tournament.players.select_related("user"))
    rows = []
    for discipline in tournament.disciplines.all():
        rows.append(
            {
                "discipline": discipline,
                "winner": winners.get(discipline.id),
                "players": players,
            }
        )
    return rows


def _scoreboard(tournament: Tournament) -> list[dict]:
    players = list(tournament.players.select_related("user"))
    win_counts = {player.user_id: 0 for player in players}
    for result in tournament.discipline_results.all():
        if result.winner_id in win_counts:
            win_counts[result.winner_id] += 1

    return [
        {"user": player.user, "score": win_counts[player.user_id]}
        for player in players
    ]


@login_required
@require_POST
def tournament_create(request: HttpRequest) -> HttpResponse:
    tournament = Tournament.create_with_host(request.user)
    return redirect("tournament_lobby", pk=tournament.pk)


@login_required
@require_POST
def tournament_join(request: HttpRequest) -> HttpResponse:
    code = (request.POST.get("invite_code") or "").strip().upper()
    if not code:
        messages.error(request, "Enter an invite code.")
        return redirect("home")

    tournament = Tournament.objects.filter(invite_code=code).first()
    if tournament is None:
        messages.error(request, "Invalid invite code.")
        return redirect("home")

    if tournament.status == Tournament.STATUS_ACTIVE:
        messages.error(request, "This tournament has already started.")
        return redirect("home")

    if tournament.status == Tournament.STATUS_FINISHED:
        messages.error(request, "This tournament has already finished.")
        return redirect("home")

    existing = _get_membership(tournament, request.user)
    if existing:
        if tournament.status == Tournament.STATUS_ACTIVE:
            return redirect("tournament_detail", pk=tournament.pk)
        return redirect("tournament_lobby", pk=tournament.pk)

    if tournament.player_count() >= 2:
        messages.error(request, "This tournament already has two players.")
        return redirect("home")

    with transaction.atomic():
        TournamentPlayer.objects.create(tournament=tournament, user=request.user)
        if tournament.status == Tournament.STATUS_WAITING:
            tournament.status = Tournament.STATUS_SELECTING
            tournament.save(update_fields=["status"])

    return redirect("tournament_lobby", pk=tournament.pk)


@login_required
@require_GET
def tournament_lobby(request: HttpRequest, pk: int) -> HttpResponse:
    tournament = get_object_or_404(
        Tournament.objects.prefetch_related("players__user", "players__selected_disciplines"),
        pk=pk,
    )
    player = _get_membership(tournament, request.user)
    if player is None:
        messages.error(request, "You are not part of this tournament.")
        return redirect("home")

    if tournament.status == Tournament.STATUS_ACTIVE:
        return redirect("tournament_detail", pk=tournament.pk)

    if tournament.status == Tournament.STATUS_FINISHED:
        return redirect("tournament_detail", pk=tournament.pk)

    disciplines = Discipline.objects.all()
    selected_ids = set(player.selected_disciplines.values_list("id", flat=True))
    opponent = tournament.players.exclude(user=request.user).select_related("user").first()

    return render(
        request,
        "tournaments/lobby.html",
        {
            "tournament": tournament,
            "player": player,
            "opponent": opponent,
            "disciplines": disciplines,
            "selected_ids": selected_ids,
            "can_ready": opponent is not None and not player.is_ready,
            "status_url": reverse("tournament_status", kwargs={"pk": tournament.pk}),
            "detail_url": reverse("tournament_detail", kwargs={"pk": tournament.pk}),
        },
    )

def speedrun_search(request):
    client = SpeedrunClient()
    query = request.GET.get('q')
    if query:
        results = client.get_game_search_results(query)
    else:
        results = []
        
    return JsonResponse(results, safe=False)


@require_POST
def tournament_speedrun_create(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    Discipline.objects.get_or_create(
                name=request.POST.get('gameName'),
                defaults={"description": 'this is discipline created through speedrun.com (change it to rules url)'},
            )

    return redirect("tournament_lobby", pk=tournament.pk)
    

@login_required
@require_POST
def tournament_ready(request: HttpRequest, pk: int) -> HttpResponse:
    tournament = get_object_or_404(Tournament, pk=pk)
    player = _get_membership(tournament, request.user)
    if player is None:
        messages.error(request, "You are not part of this tournament.")
        return redirect("home")

    if tournament.status == Tournament.STATUS_ACTIVE:
        return redirect("tournament_detail", pk=tournament.pk)

    if tournament.status == Tournament.STATUS_FINISHED:
        return redirect("tournament_detail", pk=tournament.pk)

    if tournament.player_count() < 2:
        messages.error(request, "Wait for your opponent to join before ready.")
        return redirect("tournament_lobby", pk=tournament.pk)

    if player.is_ready:
        return redirect("tournament_lobby", pk=tournament.pk)

    discipline_ids = request.POST.getlist("disciplines")
    disciplines = Discipline.objects.filter(id__in=discipline_ids)
    if not disciplines.exists():
        messages.error(request, "Select at least one discipline.")
        return redirect("tournament_lobby", pk=tournament.pk)

    with transaction.atomic():
        player.selected_disciplines.set(disciplines)
        player.is_ready = True
        player.save(update_fields=["is_ready"])
        if tournament.status == Tournament.STATUS_WAITING:
            tournament.status = Tournament.STATUS_SELECTING
            tournament.save(update_fields=["status"])
        activated = tournament.activate_if_ready()

    if activated:
        return redirect("tournament_detail", pk=tournament.pk)

    messages.success(request, "You're ready. Waiting for your opponent.")
    return redirect("tournament_lobby", pk=tournament.pk)


@login_required
@require_GET
def tournament_detail(request: HttpRequest, pk: int) -> HttpResponse:
    tournament = get_object_or_404(
        Tournament.objects.select_related("host").prefetch_related(
            "disciplines",
            "players__user",
            "discipline_results__winner",
        ),
        pk=pk,
    )
    if _get_membership(tournament, request.user) is None:
        messages.error(request, "You are not part of this tournament.")
        return redirect("home")

    if tournament.status not in (Tournament.STATUS_ACTIVE, Tournament.STATUS_FINISHED):
        return redirect("tournament_lobby", pk=tournament.pk)

    return render(
        request,
        "tournaments/detail.html",
        {
            "tournament": tournament,
            "discipline_rows": _discipline_rows(tournament),
            "scoreboard": _scoreboard(tournament),
            "discipline_count": tournament.disciplines.count(),
        },
    )


@login_required
@require_POST
def tournament_set_discipline_winner(request: HttpRequest, pk: int) -> HttpResponse:
    tournament = get_object_or_404(Tournament, pk=pk)
    if _get_membership(tournament, request.user) is None:
        messages.error(request, "You are not part of this tournament.")
        return redirect("home")

    if tournament.status != Tournament.STATUS_ACTIVE:
        messages.error(request, "Winners can only be set while the tournament is active.")
        return redirect("tournament_detail", pk=tournament.pk)

    try:
        discipline_id = int(request.POST.get("discipline_id", ""))
        winner_id = int(request.POST.get("winner_id", ""))
    except (TypeError, ValueError):
        messages.error(request, "Invalid winner selection.")
        return redirect("tournament_detail", pk=tournament.pk)

    if not tournament.disciplines.filter(id=discipline_id).exists():
        messages.error(request, "That discipline is not part of this tournament.")
        return redirect("tournament_detail", pk=tournament.pk)

    if not tournament.players.filter(user_id=winner_id).exists():
        messages.error(request, "Winner must be one of the tournament players.")
        return redirect("tournament_detail", pk=tournament.pk)

    TournamentDisciplineResult.objects.update_or_create(
        tournament=tournament,
        discipline_id=discipline_id,
        defaults={"winner_id": winner_id},
    )
    return redirect("tournament_detail", pk=tournament.pk)


@login_required
@require_POST
def tournament_finish(request: HttpRequest, pk: int) -> HttpResponse:
    tournament = get_object_or_404(Tournament, pk=pk)
    if _get_membership(tournament, request.user) is None:
        messages.error(request, "You are not part of this tournament.")
        return redirect("home")

    if tournament.status == Tournament.STATUS_FINISHED:
        return redirect("tournament_detail", pk=tournament.pk)

    if tournament.status != Tournament.STATUS_ACTIVE:
        messages.error(request, "Only an active tournament can be finished.")
        return redirect("tournament_lobby", pk=tournament.pk)

    tournament.finish()
    messages.success(request, "Tournament finished.")
    return redirect("tournament_detail", pk=tournament.pk)


@login_required
@require_GET
def tournament_status(request: HttpRequest, pk: int) -> JsonResponse:
    tournament = get_object_or_404(
        Tournament.objects.prefetch_related("players"),
        pk=pk,
    )
    if _get_membership(tournament, request.user) is None:
        return JsonResponse({"error": "forbidden"}, status=403)

    opponent_joined = tournament.player_count() >= 2
    both_ready = tournament.both_players_ready()
    active = tournament.status == Tournament.STATUS_ACTIVE

    if both_ready and not active:
        tournament.activate_if_ready()
        tournament.refresh_from_db()
        active = tournament.status == Tournament.STATUS_ACTIVE

    payload = {
        "status": tournament.status,
        "opponent_joined": opponent_joined,
        "both_ready": both_ready or active,
        "active": active,
        "redirect_url": reverse("tournament_detail", kwargs={"pk": tournament.pk})
        if active
        else None,
        "reload": opponent_joined and tournament.status == Tournament.STATUS_SELECTING,
    }
    return JsonResponse(payload)
