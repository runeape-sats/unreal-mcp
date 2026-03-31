---- MODULE CastleConstruction ----
EXTENDS FiniteSets, Sequences, TLC

RequiredActors == {
  "Keep",
  "Gatehouse",
  "WallNorth",
  "WallSouthWest",
  "WallSouthEast",
  "WallEast",
  "WallWest",
  "TowerNorthWest",
  "TowerNorthEast",
  "TowerSouthWest",
  "TowerSouthEast",
  "RoofKeep",
  "RoofNorthWest",
  "RoofNorthEast",
  "RoofSouthWest",
  "RoofSouthEast"
}

LayoutVariants == {"classic", "courtyard", "bastion", "longhall"}

SizeVariants == {"compact", "standard", "grand"}

PaletteVariants == {"granite", "sandstone", "moss", "obsidian"}

VariantActorSet(layoutChoice, sizeChoice, paletteChoice) ==
  IF layoutChoice \in LayoutVariants /\ sizeChoice \in SizeVariants /\ paletteChoice \in PaletteVariants
  THEN RequiredActors
  ELSE {}

VARIABLES phase, built, verificationPassed, failed, retries, rebuildRequested, layout, size, palette

Init ==
  /\ phase = "Idle"
  /\ built = {}
  /\ verificationPassed = FALSE
  /\ failed = {}
  /\ retries = [actor \in RequiredActors |-> 0]
  /\ rebuildRequested = FALSE
  /\ layout = "classic"
  /\ size = "standard"
  /\ palette = "granite"

ConfigureVariation(layoutChoice, sizeChoice, paletteChoice) ==
  /\ phase = "Idle"
  /\ layoutChoice \in LayoutVariants
  /\ sizeChoice \in SizeVariants
  /\ paletteChoice \in PaletteVariants
  /\ layout' = layoutChoice
  /\ size' = sizeChoice
  /\ palette' = paletteChoice
  /\ UNCHANGED <<phase, built, verificationPassed, failed, retries, rebuildRequested>>

StartBuild ==
  /\ phase = "Idle"
  /\ phase' = "Building"
  /\ UNCHANGED <<built, verificationPassed, failed, retries, rebuildRequested, layout, size, palette>>

AddActor(actor) ==
  /\ phase = "Building"
  /\ actor \in RequiredActors
  /\ actor \notin built
  /\ actor \notin failed
  /\ built' = built \cup {actor}
  /\ UNCHANGED <<phase, verificationPassed, failed, retries, rebuildRequested, layout, size, palette>>

RecordFailure(actor) ==
  /\ phase = "Building"
  /\ actor \in RequiredActors
  /\ actor \notin built
  /\ actor \notin failed
  /\ failed' = failed \cup {actor}
  /\ retries' = [retries EXCEPT ![actor] = @ + 1]
  /\ UNCHANGED <<phase, built, verificationPassed, rebuildRequested, layout, size, palette>>

RetryFailedActor(actor) ==
  /\ phase = "Building"
  /\ actor \in failed
  /\ retries[actor] < 3
  /\ failed' = failed \ {actor}
  /\ UNCHANGED <<phase, built, verificationPassed, retries, rebuildRequested, layout, size, palette>>

GiveUp(actor) ==
  /\ phase = "Building"
  /\ actor \in failed
  /\ retries[actor] >= 3
  /\ phase' = "Failed"
  /\ verificationPassed' = FALSE
  /\ rebuildRequested' = TRUE
  /\ UNCHANGED <<built, failed, retries, layout, size, palette>>

BeginVerification ==
  /\ phase = "Building"
  /\ built = RequiredActors
  /\ failed = {}
  /\ phase' = "Verifying"
  /\ UNCHANGED <<built, verificationPassed, failed, retries, rebuildRequested, layout, size, palette>>

FinishVerification ==
  /\ phase = "Verifying"
  /\ verificationPassed' = (built = RequiredActors)
  /\ phase' = IF verificationPassed' THEN "Completed" ELSE "Failed"
  /\ rebuildRequested' = ~verificationPassed'
  /\ UNCHANGED <<built, failed, retries, layout, size, palette>>

StartRebuild ==
  /\ phase = "Failed"
  /\ rebuildRequested = TRUE
  /\ phase' = "Building"
  /\ built' = {}
  /\ failed' = {}
  /\ verificationPassed' = FALSE
  /\ rebuildRequested' = FALSE
  /\ UNCHANGED <<retries, layout, size, palette>>

Reset ==
  /\ phase \in {"Completed", "Failed"}
  /\ phase' = "Idle"
  /\ built' = {}
  /\ verificationPassed' = FALSE
  /\ failed' = {}
  /\ retries' = [actor \in RequiredActors |-> 0]
  /\ rebuildRequested' = FALSE
  /\ layout' = "classic"
  /\ size' = "standard"
  /\ palette' = "granite"

Next ==
  \/ \E layoutChoice \in LayoutVariants, sizeChoice \in SizeVariants, paletteChoice \in PaletteVariants:
       ConfigureVariation(layoutChoice, sizeChoice, paletteChoice)
  \/ StartBuild
  \/ \E actor \in RequiredActors: AddActor(actor)
  \/ \E actor \in RequiredActors: RecordFailure(actor)
  \/ \E actor \in RequiredActors: RetryFailedActor(actor)
  \/ \E actor \in RequiredActors: GiveUp(actor)
  \/ BeginVerification
  \/ FinishVerification
  \/ StartRebuild
  \/ Reset

Spec == Init /\ [][Next]_<<phase, built, verificationPassed, failed, retries, rebuildRequested, layout, size, palette>>

ActorsWithinPlan == built \subseteq RequiredActors

FailuresWithinPlan == failed \subseteq RequiredActors

CompletedMeansAllActors ==
  phase = "Completed" => built = RequiredActors

VerificationMatchesState ==
  verificationPassed => phase = "Completed"

FailureRequiresWork ==
  phase = "Failed" => failed # {} \/ rebuildRequested

RetriesBounded ==
  \A actor \in RequiredActors: retries[actor] <= 3

RebuildResetsBuildSet ==
  rebuildRequested => phase = "Failed" \/ phase = "Building"

ChosenLayoutValid ==
  layout \in LayoutVariants

ChosenSizeValid ==
  size \in SizeVariants

ChosenPaletteValid ==
  palette \in PaletteVariants

VariantPreservesCoreActors ==
  VariantActorSet(layout, size, palette) = RequiredActors

EventuallyComplete == <>(phase = "Completed")

====