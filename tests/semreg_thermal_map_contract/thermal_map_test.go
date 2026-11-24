package semreg_thermal_map_contract

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"strings"
	"testing"

	semreg "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/graph"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/projection"
)

const semregModule = "github.com/Project-Helianthus/helianthus-semreg"

// unresolvedNativeRelation is the preserved eBUS attachment reason. It is not
// the reason of a SemReg catalog entry: the pinned member facts have none.
const unresolvedNativeRelation = semreg.DefinitionID("catalog.reason.subject_unresolved")

type mappingIndex struct {
	Pack      semreg.PackRef `json:"pack"`
	Mappings  []mapping      `json:"mappings"`
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
	NativeKey   string          `json:"native_key"`
	NativeValue json.RawMessage `json:"native_value"`
	SemregFact  *string         `json:"semreg_fact"`
	Target      *target         `json:"target"`
	EbusMapping *ebusMapping    `json:"ebus_mapping"`
}

// elementRef is the pack owner, identifier and version of a catalog reference.
type elementRef struct {
	Owner struct {
		Kind string         `json:"kind"`
		Pack semreg.PackRef `json:"pack"`
	} `json:"owner"`
	ID      semreg.DefinitionID    `json:"id"`
	Version semreg.SemanticVersion `json:"version"`
}

// factSubject is the subject copied from a fact's catalog attributes.
type factSubject struct {
	Status             string      `json:"status"`
	Dimension          *elementRef `json:"dimension"`
	Kind               string      `json:"kind"`
	QualifierDimension *elementRef `json:"qualifier_dimension"`
}

// target is a row's copy of the element-inventory definition of its fact.
// It is not the eBUS native attachment.
type target struct {
	Definition  semreg.DefinitionRef `json:"definition"`
	ElementKind string               `json:"element_kind"`
	Disposition string               `json:"disposition"`
	Planes      []string             `json:"planes"`
	Reason      *string              `json:"reason"`
	Subject     *factSubject         `json:"subject"`
}

// ebusMapping keeps the unresolved native relation and the withheld projection
// apart from the catalog copy. It names no relation instance and no resource.
type ebusMapping struct {
	NativeRelation struct {
		Status string               `json:"status"`
		Reason *semreg.DefinitionID `json:"reason"`
	} `json:"native_relation"`
	Projection projection.ProjectionDisposition `json:"projection"`
}

// loadInventory reads the element inventory bytes from the pinned SemReg
// module and loads them; Load accepts only the bytes with the pinned digest.
func loadInventory(t *testing.T) *graph.Catalog {
	t.Helper()
	out, err := exec.Command("go", "list", "-m", "-f", "{{.Dir}}", semregModule).Output()
	if err != nil {
		t.Fatalf("locate the pinned SemReg module: %v", err)
	}
	raw, err := os.ReadFile(filepath.Join(strings.TrimSpace(string(out)), "fixtures", "v1", "element-catalog-v1.json"))
	if err != nil {
		t.Fatal(err)
	}
	catalog, err := graph.Load(raw)
	if err != nil {
		t.Fatalf("element inventory of the pinned SemReg module does not load: %v", err)
	}
	if catalog.Digest() != graph.PinnedDigest {
		t.Fatalf("element inventory digest = %s, want the pinned digest %s", catalog.Digest(), graph.PinnedDigest)
	}
	return catalog
}

// checkTarget compares a row's target with the element inventory entry of its
// definition, member by member, including the resolved resource dimension.
func checkTarget(catalog *graph.Catalog, row target) error {
	entry, ok := catalog.PackEntry(row.Definition)
	if !ok {
		return fmt.Errorf("%s/%s %s@%s is not in the element inventory", row.Definition.Pack.ID, row.Definition.Pack.Version, row.Definition.ID, row.Definition.Version)
	}
	if string(entry.ElementKind) != row.ElementKind {
		return fmt.Errorf("%s: element kind %q, inventory %q", row.Definition.ID, row.ElementKind, entry.ElementKind)
	}
	if string(entry.Disposition) != row.Disposition {
		return fmt.Errorf("%s: disposition %q, inventory %q", row.Definition.ID, row.Disposition, entry.Disposition)
	}
	planes := make([]string, len(entry.Planes))
	for i, plane := range entry.Planes {
		planes[i] = string(plane)
	}
	if !slices.Equal(planes, row.Planes) || row.Planes == nil {
		return fmt.Errorf("%s: planes %v, inventory %v", row.Definition.ID, row.Planes, planes)
	}
	reason := ""
	if row.Reason != nil {
		reason = *row.Reason
	}
	if string(entry.Reason) != reason || (row.Reason != nil && reason == "") {
		return fmt.Errorf("%s: reason %q, inventory %q", row.Definition.ID, reason, entry.Reason)
	}
	if entry.ElementKind != graph.KindFact {
		return fmt.Errorf("%s: element kind %q, want a fact", row.Definition.ID, entry.ElementKind)
	}
	if err := checkSubject(entry, row); err != nil {
		return err
	}
	return nil
}

// checkSubject compares the copied fact subject with the inventory subject.
func checkSubject(entry graph.Element, row target) error {
	if entry.Fact == nil {
		return fmt.Errorf("%s: inventory fact attributes are absent", row.Definition.ID)
	}
	subject := entry.Fact.Subject
	if row.Subject == nil {
		return fmt.Errorf("%s: target omits the inventory subject", row.Definition.ID)
	}
	if string(subject.Status) != row.Subject.Status {
		return fmt.Errorf("%s: subject status %q, inventory %q", row.Definition.ID, row.Subject.Status, subject.Status)
	}
	if !sameElementRef(row.Subject.Dimension, subject.Dimension) {
		return fmt.Errorf("%s: resource dimension differs from the inventory", row.Definition.ID)
	}
	if row.Subject.Kind != string(subject.Kind) {
		return fmt.Errorf("%s: resource kind %q, inventory %q", row.Definition.ID, row.Subject.Kind, subject.Kind)
	}
	if !sameElementRef(row.Subject.QualifierDimension, subject.QualifierDimension) {
		return fmt.Errorf("%s: qualifier dimension differs from the inventory", row.Definition.ID)
	}
	if subject.Status != graph.SubjectResolved || subject.Dimension == nil {
		return fmt.Errorf("%s: inventory subject %q is not a resolved resource dimension", row.Definition.ID, subject.Status)
	}
	return nil
}

func sameElementRef(got *elementRef, want *graph.ElementRef) bool {
	if (got == nil) != (want == nil) {
		return false
	}
	if got == nil {
		return true
	}
	return got.Owner.Kind == string(want.Owner.Kind) && got.Owner.Pack == want.Owner.Pack && got.ID == want.ID && got.Version == want.Version
}

// checkEbusMapping requires an unresolved native relation and a withheld
// projection that names neither a relation instance nor a resource.
func checkEbusMapping(mapping ebusMapping, fact semreg.DefinitionID) error {
	if mapping.NativeRelation.Status != "unresolved" {
		return fmt.Errorf("native relation status %q, want unresolved", mapping.NativeRelation.Status)
	}
	if mapping.NativeRelation.Reason == nil || *mapping.NativeRelation.Reason != unresolvedNativeRelation {
		return fmt.Errorf("native relation reason %v, want %s", mapping.NativeRelation.Reason, unresolvedNativeRelation)
	}
	if err := mapping.NativeRelation.Reason.Validate(); err != nil {
		return fmt.Errorf("native relation reason: %v", err)
	}
	if err := mapping.Projection.Validate(); err != nil {
		return fmt.Errorf("projection: %v", err)
	}
	disposition := mapping.Projection
	if disposition.Kind != projection.ItemFact || disposition.ItemID != fact {
		return fmt.Errorf("projection names another item")
	}
	if disposition.Outcome != projection.ProjectionWithheld || len(disposition.SourceKeys) != 0 || len(disposition.Loss) != 0 {
		return fmt.Errorf("unresolved native relation withholds the projection with no source key and no loss")
	}
	if disposition.Reason == nil || *disposition.Reason != *mapping.NativeRelation.Reason {
		return fmt.Errorf("projection reason differs from the native relation reason")
	}
	if disposition.Relations != nil || disposition.Resources != nil {
		return fmt.Errorf("withheld projection names a resource or a relation")
	}
	return nil
}

func TestThermalRowTargetsMatchTheElementInventory(t *testing.T) {
	catalog := loadInventory(t)
	index := loadIndex(t)
	withTarget := 0
	for _, row := range index.Mappings {
		if row.Target == nil {
			if row.SemregFact != nil || row.EbusMapping != nil {
				t.Fatalf("%s names a fact or an eBUS mapping without a target", row.NativeKey)
			}
			continue
		}
		withTarget++
		if row.SemregFact == nil || semreg.DefinitionID(*row.SemregFact) != row.Target.Definition.ID {
			t.Fatalf("%s: semreg_fact differs from the target definition", row.NativeKey)
		}
		if row.EbusMapping == nil {
			t.Fatalf("%s: catalog copy has no separate eBUS mapping", row.NativeKey)
		}
		if row.Target.Definition.Pack != index.Pack {
			t.Fatalf("%s: target pack %v, index pack %v", row.NativeKey, row.Target.Definition.Pack, index.Pack)
		}
		if err := checkTarget(catalog, *row.Target); err != nil {
			t.Fatalf("%s: %v", row.NativeKey, err)
		}
		if err := checkEbusMapping(*row.EbusMapping, row.Target.Definition.ID); err != nil {
			t.Fatalf("%s: %v", row.NativeKey, err)
		}
		if row.Target.Disposition == string(graph.DispositionUnknown) {
			t.Fatalf("%s: catalog copy must not stand in for the unresolved native relation", row.NativeKey)
		}
	}
	if withTarget != 2 {
		t.Fatalf("rows with a target = %d, want 2", withTarget)
	}
}

func TestTargetDriftInEveryMemberIsRejected(t *testing.T) {
	catalog := loadInventory(t)
	row := *loadIndex(t).Mappings[1].Target
	if err := checkTarget(catalog, row); err != nil {
		t.Fatal(err)
	}
	other := "catalog.reason.no_fact_or_relation"
	empty := ""
	for name, mutate := range map[string]func(*target){
		"pack id":        func(r *target) { r.Definition.Pack.ID = "helianthus.pack.storage" },
		"pack version":   func(r *target) { r.Definition.Pack.Version = "1.1.0" },
		"id":             func(r *target) { r.Definition.ID = "thermal.measurement.outdoor_air_temperature" },
		"version":        func(r *target) { r.Definition.Version = "1.0.1" },
		"element kind":   func(r *target) { r.ElementKind = "dimension" },
		"disposition":    func(r *target) { r.Disposition = "unknown" },
		"planes":         func(r *target) { r.Planes = []string{"control"} },
		"no planes":      func(r *target) { r.Planes = nil },
		"reason":         func(r *target) { r.Reason = &other },
		"empty reason":   func(r *target) { r.Reason = &empty },
		"no subject":     func(r *target) { r.Subject = nil },
		"subject status": func(r *target) { r.Subject.Status = "unresolved" },
		"dimension":      func(r *target) { r.Subject.Dimension.ID = "thermal.dimension.zone" },
		"resource kind":  func(r *target) { r.Subject.Kind = "resource.zone" },
		"qualifier": func(r *target) {
			qualifier := *r.Subject.Dimension
			qualifier.ID = "thermal.dimension.temperature"
			r.Subject.QualifierDimension = &qualifier
		},
	} {
		mutated := row
		mutated.Planes = slices.Clone(row.Planes)
		mutated.Subject = cloneSubject(row.Subject)
		mutate(&mutated)
		if err := checkTarget(catalog, mutated); err == nil {
			t.Errorf("%s drift is accepted", name)
		}
	}
}

func cloneSubject(subject *factSubject) *factSubject {
	if subject == nil {
		return nil
	}
	copied := *subject
	if subject.Dimension != nil {
		dimension := *subject.Dimension
		copied.Dimension = &dimension
	}
	if subject.QualifierDimension != nil {
		qualifier := *subject.QualifierDimension
		copied.QualifierDimension = &qualifier
	}
	return &copied
}

func TestDelayedEvaluationContextPreservesReceiptAndUsesElapsedMonotonic(t *testing.T) {
	index := loadIndex(t)
	observation := index.Lifecycle.RetainedNativeObservation
	evaluation := index.Lifecycle.CallerEvaluationContext
	context := semreg.EvaluationContext{EvaluatedAt: evaluation.EvaluatedAt, EvaluateMonotonic: evaluation.EvaluateMonotonic}
	if err := context.Validate(); err != nil {
		t.Fatalf("delayed caller evaluation context invalid: %v", err)
	}
	times := semreg.Times{
		ReceivedAt: observation.ReceivedAt, ReceiptMonotonic: observation.ReceiptMonotonic,
		EvaluatedAt: context.EvaluatedAt, EvaluateMonotonic: context.EvaluateMonotonic,
	}
	if err := times.Validate(); err != nil {
		t.Fatalf("retained receipt and evaluation times invalid: %v", err)
	}
	if times.ReceivedAt != observation.ReceivedAt || times.ReceiptMonotonic != observation.ReceiptMonotonic {
		t.Fatal("evaluation context overwrote the retained receipt")
	}
	if times.ReceivedAt == context.EvaluatedAt || times.ReceiptMonotonic == context.EvaluateMonotonic {
		t.Fatal("delayed evaluation must remain distinct from receipt")
	}
	elapsed, err := times.ElapsedMonotonicNS()
	if err != nil {
		t.Fatalf("elapsed monotonic freshness is invalid: %v", err)
	}
	if elapsed != "5000000000" {
		t.Fatalf("elapsed monotonic = %s, want 5000000000", elapsed)
	}
}

// checkMappedTemperature requires every field of a mapped temperature value.
// wire_type stays f32_le, unit stays degC, si_unit is kelvin, and conversion
// is degrees Celsius plus 273.15. A missing si_unit or conversion fails.
func checkMappedTemperature(raw json.RawMessage) error {
	if len(raw) == 0 || raw[0] != '{' {
		return fmt.Errorf("native value must be an object")
	}
	var fields map[string]json.RawMessage
	if err := json.Unmarshal(raw, &fields); err != nil {
		return err
	}
	if _, ok := fields["si_unit"]; !ok {
		return fmt.Errorf("mapped row lacks the SI unit")
	}
	if _, ok := fields["conversion"]; !ok {
		return fmt.Errorf("mapped row lacks the conversion")
	}
	want := map[string]string{
		"wire_type":  "f32_le",
		"unit":       "degC",
		"si_unit":    "kelvin",
		"conversion": "degrees Celsius plus 273.15",
	}
	for name, value := range want {
		var got string
		if json.Unmarshal(fields[name], &got) != nil || got != value {
			return fmt.Errorf("%s = %s, want %s", name, fields[name], value)
		}
	}
	if len(fields) != len(want) {
		return fmt.Errorf("native value members = %d, want %d", len(fields), len(want))
	}
	return nil
}

func checkUnmappedTemperature(raw json.RawMessage) error {
	if len(raw) == 0 || raw[0] != '{' {
		return fmt.Errorf("native value must be an object")
	}
	var fields map[string]json.RawMessage
	if err := json.Unmarshal(raw, &fields); err != nil {
		return err
	}
	if _, ok := fields["si_unit"]; ok {
		return fmt.Errorf("unmapped row states an SI unit")
	}
	if _, ok := fields["conversion"]; ok {
		return fmt.Errorf("unmapped row states a conversion")
	}
	var wireType, unit string
	if json.Unmarshal(fields["wire_type"], &wireType) != nil || wireType != "f32_le" ||
		json.Unmarshal(fields["unit"], &unit) != nil || unit != "degC" || len(fields) != 2 {
		return fmt.Errorf("unmapped native value = %s", raw)
	}
	return nil
}

// rejectEachMappedTemperatureField varies wire_type, unit, si_unit and conversion.
func rejectEachMappedTemperatureField(t *testing.T, raw json.RawMessage) {
	t.Helper()
	if err := checkMappedTemperature(raw); err != nil {
		t.Fatal(err)
	}
	var current map[string]any
	if err := json.Unmarshal(raw, &current); err != nil {
		t.Fatal(err)
	}
	cases := []struct {
		name   string
		mutate func(map[string]any)
	}{
		{"wire_type u16", func(m map[string]any) { m["wire_type"] = "u16" }},
		{"unit unit.celsius", func(m map[string]any) { m["unit"] = "unit.celsius" }},
		{"unit kelvin", func(m map[string]any) { m["unit"] = "kelvin" }},
		{"si_unit removed", func(m map[string]any) { delete(m, "si_unit") }},
		{"si_unit unit.celsius", func(m map[string]any) { m["si_unit"] = "unit.celsius" }},
		{"conversion removed", func(m map[string]any) { delete(m, "conversion") }},
		{"conversion degrees Celsius", func(m map[string]any) { m["conversion"] = "degrees Celsius" }},
	}
	for _, tc := range cases {
		mutated := map[string]any{}
		for key, value := range current {
			mutated[key] = value
		}
		tc.mutate(mutated)
		encoded, err := json.Marshal(mutated)
		if err != nil {
			t.Fatal(err)
		}
		if err := checkMappedTemperature(encoded); err == nil {
			t.Errorf("%s drift is accepted", tc.name)
		}
	}
}

func TestMappedRowsStateSIUnitAndConversion(t *testing.T) {
	index := loadIndex(t)
	mapped := 0
	for _, row := range index.Mappings {
		if row.SemregFact == nil {
			if err := checkUnmappedTemperature(row.NativeValue); err != nil {
				t.Fatalf("%s: %v", row.NativeKey, err)
			}
			continue
		}
		mapped++
		if err := checkMappedTemperature(row.NativeValue); err != nil {
			t.Fatalf("%s: %v", row.NativeKey, err)
		}
		rejectEachMappedTemperatureField(t, row.NativeValue)
	}
	if mapped != 2 {
		t.Fatalf("mapped rows = %d, want 2", mapped)
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
