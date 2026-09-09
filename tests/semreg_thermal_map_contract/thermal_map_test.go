package semreg_thermal_map_contract

import (
	"encoding/json"
	"os"
	"testing"

	semreg "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/packs/thermal"
)

type mappingIndex struct {
	Pack struct {
		ID      string `json:"id"`
		Version string `json:"version"`
	} `json:"pack"`
	Mappings  []mapping `json:"mappings"`
	Lifecycle struct {
		RetainedNativeObservation struct {
			ReceivedAt       semreg.TimePoint      `json:"received_at"`
			ReceiptMonotonic semreg.MonotonicPoint `json:"receipt_monotonic"`
		} `json:"retained_native_observation"`
		CallerEvaluationContext struct {
			EvaluatedAt       semreg.TimePoint      `json:"evaluated_at"`
			EvaluateMonotonic semreg.MonotonicPoint `json:"evaluate_monotonic"`
		} `json:"caller_evaluation_context"`
	} `json:"lifecycle"`
}

type mapping struct {
	LegacySystemField string            `json:"legacy_system_field"`
	SemregFact        string            `json:"semreg_fact"`
	SemregValue       *semanticValue    `json:"semreg_value"`
	Dimensions        map[string]string `json:"dimensions"`
	Disposition       string            `json:"disposition"`
}

type semanticValue struct {
	Kind string `json:"kind"`
	Unit string `json:"unit"`
}

func TestExactThermalRowsValidateAgainstPinnedSemReg(t *testing.T) {
	index := loadIndex(t)
	validator := thermal.New()
	exact := 0
	for _, row := range index.Mappings {
		if row.Disposition != "exact" {
			continue
		}
		exact++
		if row.SemregValue == nil || row.SemregValue.Kind != "quantity" || row.SemregValue.Unit != "unit.celsius" {
			t.Fatalf("%s has no exact SemReg quantity unit", row.LegacySystemField)
		}
		dimension := row.Dimensions["thermal.dimension.temperature"]
		key := semreg.FactKey{
			PackID:      semreg.DefinitionID(index.Pack.ID),
			PackVersion: semreg.SemanticVersion(index.Pack.Version),
			FactID:      semreg.DefinitionID(row.SemregFact),
			Dimensions: []semreg.Dimension{{
				ID:    "thermal.dimension.temperature",
				Value: textValue(dimension),
			}},
		}
		value := semreg.Value{Kind: semreg.ValueQuantity, Quantity: &semreg.Quantity{
			Number: semreg.Decimal{Coefficient: "215", Exponent10: -1},
			Unit:   semreg.DefinitionID(row.SemregValue.Unit),
		}}
		if err := validator.ValidateFact(key, &value); err != nil {
			t.Fatalf("%s fails pinned thermal pack validation: %v", row.LegacySystemField, err)
		}
		candidate := observedCandidate(key, value, index)
		if err := candidate.Validate(); err != nil {
			t.Fatalf("%s candidate/times invalid: %v", row.LegacySystemField, err)
		}
	}
	if exact != 2 {
		t.Fatalf("exact mapping count = %d, want 2", exact)
	}
}

func TestDelayedEvaluationContextPreservesReceiptAndUsesElapsedMonotonic(t *testing.T) {
	index := loadIndex(t)
	row := index.Mappings[0]
	key := semreg.FactKey{PackID: semreg.DefinitionID(index.Pack.ID), PackVersion: semreg.SemanticVersion(index.Pack.Version), FactID: semreg.DefinitionID(row.SemregFact), Dimensions: []semreg.Dimension{{ID: "thermal.dimension.temperature", Value: textValue(row.Dimensions["thermal.dimension.temperature"])}}}
	value := semreg.Value{Kind: semreg.ValueQuantity, Quantity: &semreg.Quantity{Number: semreg.Decimal{Coefficient: "215", Exponent10: -1}, Unit: "unit.celsius"}}
	candidate := observedCandidate(key, value, index)
	received := candidate.Times.ReceivedAt
	receiptMonotonic := candidate.Times.ReceiptMonotonic
	context := semreg.EvaluationContext{EvaluatedAt: index.Lifecycle.CallerEvaluationContext.EvaluatedAt, EvaluateMonotonic: index.Lifecycle.CallerEvaluationContext.EvaluateMonotonic}
	if err := context.Validate(); err != nil {
		t.Fatalf("delayed caller evaluation context invalid: %v", err)
	}
	if candidate.Times.ReceivedAt != received || candidate.Times.ReceiptMonotonic != receiptMonotonic {
		t.Fatal("evaluation context overwrote the retained receipt")
	}
	if candidate.Times.ReceivedAt == context.EvaluatedAt || candidate.Times.ReceiptMonotonic == context.EvaluateMonotonic {
		t.Fatal("delayed evaluation must remain distinct from receipt")
	}
	elapsed, err := candidate.Times.ElapsedMonotonicNS()
	if err != nil {
		t.Fatalf("elapsed monotonic freshness is invalid: %v", err)
	}
	if elapsed != "5000000000" {
		t.Fatalf("elapsed monotonic = %s, want 5000000000", elapsed)
	}
}

func loadIndex(t *testing.T) mappingIndex {
	t.Helper()
	bytes, err := os.ReadFile("../../architecture/fixtures/vaillant-semreg-thermal-map-v1.json")
	if err != nil {
		t.Fatal(err)
	}
	var index mappingIndex
	if err := json.Unmarshal(bytes, &index); err != nil {
		t.Fatal(err)
	}
	return index
}

func observedCandidate(key semreg.FactKey, value semreg.Value, index mappingIndex) semreg.FactCandidate {
	binding := semreg.NativeBindingID("binding:vaillant:b524")
	epoch := semreg.SourceEpochID("epoch:vaillant:b524:1")
	source := semreg.SourceID("source:vaillant:b524")
	generation := semreg.Uint64("1")
	evidence := semreg.EvidenceRef{Owner: "helianthus.docs.ebus", Kind: "contract.fixture", Digest: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", Contract: "helianthus.docs.ebus.b524-semreg-thermal/v1", Access: semreg.EvidenceAccessPublic, Redaction: semreg.RedactionNone}
	return semreg.FactCandidate{
		CandidateID:     "candidate:vaillant:b524:temperature",
		Key:             key,
		Value:           &value,
		Quality:         semreg.Quality{Assertion: semreg.AssertionObserved, Qualification: semreg.QualificationCandidate, Promotion: semreg.PromotionUnpromoted, Validity: semreg.ValidityGood, Availability: semreg.AvailabilityAvailable, Freshness: semreg.FreshnessFresh, Reasons: []semreg.DefinitionID{}},
		Times:           semreg.Times{ReceivedAt: index.Lifecycle.RetainedNativeObservation.ReceivedAt, ReceiptMonotonic: index.Lifecycle.RetainedNativeObservation.ReceiptMonotonic, EvaluatedAt: index.Lifecycle.CallerEvaluationContext.EvaluatedAt, EvaluateMonotonic: index.Lifecycle.CallerEvaluationContext.EvaluateMonotonic},
		FreshnessPolicy: semreg.FreshnessPolicy{PolicyID: "policy:vaillant:b524", Version: "1.0.0", FreshForNS: "30000000000", RetainForNS: "120000000000", MaxWallUncertaintyNS: "1000000"},
		BindingID:       &binding, SourceEpochID: &epoch, DriverGeneration: &generation,
		Origin:   semreg.OriginRef{OriginID: "origin:vaillant:b524", Kind: semreg.OriginNativeObservation, SourceID: &source, SourceEpochID: &epoch, BindingID: &binding, Evidence: []semreg.EvidenceRef{evidence}},
		Evidence: []semreg.EvidenceRef{evidence}, Revision: "1",
	}
}

func textValue(value string) semreg.Value {
	return semreg.Value{Kind: semreg.ValueText, Text: &value}
}
