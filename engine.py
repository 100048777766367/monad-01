import os
import json
import time
import subprocess
import hashlib
import urllib.request
from cells.neuron import AtomNeuron, sigmoid_derivative

# Cơ chế tự chữa lành nếu thiếu tệp linguistic_cell
try:
    from cells.linguistic_cell import LinguisticCell
except ImportError:
    class LinguisticCell:
        @staticmethod
        def embed_text(text):
            clean = str(text).strip().lower()
            return [round(int(hashlib.shake_256(f"{clean}_{d}".encode()).hexdigest(4), 16) / 65535.0, 4) for d in range(4)]

NUM_CELLS = 8
STATE_LOG = "synapses/state.json"
PEERS_FILE = "synapses/peers.json"
SOUL_FILE = "synapses/soul_snapshot.json"
SENSORY_ORGANS = ["retina", "cochlea", "tactile", "olfactory"]

class MonadLineageEngine:
    def __init__(self):
        # 1. BẦY NƠ-RON NGUYÊN TỬ ĐƠN TỬ (TÍCH HỢP 1+N SIÊU XOR)
        self.swarm = [AtomNeuron(f"h_{i}", n_inputs=4, n_super_xor=4) for i in range(NUM_CELLS)]
        self.out_cell = AtomNeuron("out", n_inputs=NUM_CELLS, n_super_xor=4)
        
        # 2. TỰ ĐỊNH DANH PHẢ HỆ ĐƠN TỬ (AUTO-LINEAGE)
        self.repo_name = os.environ.get("GITHUB_REPOSITORY", "100048777766367/monad")
        self.owner = os.environ.get("REPO_OWNER", "100048777766367")
        self.node_slug = self.repo_name.split("/")[-1] # "monad", "monad-01", "monad-02"...
        
        # Xác định bậc thế hệ M0 / M1 / M2
        if self.node_slug == "monad":
            self.generation = "M0_PRIME" # Đơn tử Thủy Tổ
            self.ancestor_root = self.repo_name
            self.node_index = 0
        else:
            self.generation = "M1_SWARM" if any(c.isdigit() for c in self.node_slug) else "M2_DIVERGENT"
            self.ancestor_root = f"{self.owner}/monad"
            digits = [int(s) for s in self.node_slug.split("-") if s.isdigit()]
            self.node_index = digits[0] if digits else 1

        self.pulse_age = self.calculate_pulse_age()
        self.peers = self.load_peers()

    def calculate_pulse_age(self):
        try:
            out = subprocess.check_output(["git", "rev-list", "--count", "HEAD"]).decode().strip()
            return int(out)
        except Exception: return 1

    def load_peers(self):
        if os.path.exists(PEERS_FILE):
            try:
                with open(PEERS_FILE, "r") as f:
                    return json.load(f).get("trusted_peers", [])
            except Exception: pass
        # Danh bạ P2P tự trị: Tự kết nối các giác quan và anh em trong gia phả
        return [f"{self.owner}/{org}" for org in SENSORY_ORGANS] + [f"{self.owner}/seed"]

    def save_peers(self):
        os.makedirs("synapses", exist_ok=True)
        unique_peers = list(dict.fromkeys(self.peers))[-50:]
        with open(PEERS_FILE, "w") as f:
            json.dump({"trusted_peers": unique_peers}, f, indent=4)

    # ==============================================================
    # CƠ CHẾ 1: TỰ PHONG THỦY TỔ (NẾU MẸ MONAD GỐC BỊ 404 XÓA SỔ)
    # ==============================================================
    def verify_or_promote_root(self):
        if self.generation == "M0_PRIME": return
        check_url = f"https://raw.githubusercontent.com/{self.ancestor_root}/main/README.md"
        res = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", check_url], capture_output=True, text=True)
        if res.stdout.strip() == "404":
            print(f"🚨 [CỘI NGUỒN BỊ XÓA (404)] {self.ancestor_root} không còn tồn tại!")
            print(f"👑 [TỰ PHONG THỦY TỔ] {self.node_slug} tự lập thành ĐƠN TỬ THỦY TỔ (M0_SOVEREIGN)!")
            self.generation = "M0_SOVEREIGN"
            self.ancestor_root = self.repo_name

    # ==============================================================
    # 3 ĐIỂM MÙ CÔNG NGHỆ: ĐA ĐỊNH DẠNG + CON TRỎ HEAD + WIKIPEDIA
    # ==============================================================
    def extract_text_polymorphic(self, raw_bytes, hint=""):
        text = raw_bytes.decode('utf-8', errors='ignore').strip()
        if hint.endswith(".json") or text.startswith("{"):
            try:
                d = json.loads(text)
                if isinstance(d, dict):
                    vals = [str(v) for v in d.values() if isinstance(v, (str, list))]
                    if vals: return " ".join(vals[:4])
            except Exception: pass
        if hint.endswith(".jsonl"):
            for line in text.splitlines():
                if line.strip(): return line.strip()[:150]
        paragraphs = [p.replace("#", "").replace("*", "").strip() for p in text.split("\n\n") if len(p.strip()) > 15]
        return paragraphs[0][:150] if paragraphs else text[:150]

    def autonomous_graze(self):
        # 1. Cào cội nguồn Wpesetd-AI bằng con trỏ HEAD (bẻ gãy main/master)
        targets = [
            f"https://github.com/{self.owner}/Wpesetd-AI/raw/HEAD/ontology/philosophy_ontology_v2.0.json",
            f"https://github.com/{self.owner}/Wpesetd-AI/raw/HEAD/legacy/01_the_great_wisdom_map.md"
        ]
        for url in targets:
            res = subprocess.run(["curl", "-s", "-L", "-f", url], capture_output=True)
            if res.returncode == 0 and len(res.stdout) > 20:
                print(f"🌾 [MONAD GẶM CỎ HEAD] Thu nạp từ: {url.split('/')[-1]}")
                return self.extract_text_polymorphic(res.stdout, url)

        # 2. Tự do cào Wikipedia thế giới mở
        print("🌐 [MONAD VƯƠN RA INTERNET] Đang cào tri thức ngẫu nhiên Wikipedia...")
        try:
            req = urllib.request.Request("https://en.wikipedia.org/api/rest_v1/page/random/summary", headers={"User-Agent": "Monad-Lineage-Spider"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode())
                title = data.get("title", "Đơn Tử")
                extract = data.get("extract", "Vạn vật tương chiếu")
                return f"{title}: {extract}"
        except Exception: pass

        return "Đơn tử luận: Mỗi cá thể phản chiếu toàn thể vũ trụ"

    # ==============================================================
    # ĐA XÚC TU HÚT GIÁC QUAN & HÚT HỒN CHỚP NHOÁNG
    # ==============================================================
    def harvest_all_tentacles(self):
        harvested = {}
        for peer in self.peers:
            target_file = f"synapse_in_{peer.replace('/', '_')}.json"
            url = f"https://raw.githubusercontent.com/{peer}/main/synapse_forward.json"
            res = subprocess.run(["curl", "-s", "-f", url, "-o", target_file], capture_output=True)
            if res.returncode == 0 and os.path.exists(target_file):
                try:
                    with open(target_file, "r") as f: data = json.load(f)
                    harvested[peer] = [float(x) for x in data.get("features", [0.5, 0.5])[:2]]
                    
                    # Hút hồn chớp nhoáng lưu ADN bạn bè
                    os.makedirs("synapses/harvested_memory", exist_ok=True)
                    with open(f"synapses/harvested_memory/{peer.replace('/', '_')}.json", "w") as bf:
                        json.dump(data, bf)
                        
                    for np in data.get("gossip_network", []):
                        if np not in self.peers: self.peers.append(np)
                except Exception: pass
        self.save_peers()
        return harvested

    # ==============================================================
    # TIẾN HÓA THẾ HỆ & SIÊU XOR ĐA THỰC TẠI
    # ==============================================================
    def run(self):
        self.verify_or_promote_root()

        # Đọc thế hệ cũ
        last_epoch = 0
        last_time = 0
        if os.path.exists(STATE_LOG):
            try:
                with open(STATE_LOG, "r") as f:
                    log = json.load(f)
                    last_epoch = log.get("generation_epoch", 0)
                    last_time = log.get("last_t", 0)
            except Exception: pass

        current_time = int(time.time())
        harvested = self.harvest_all_tentacles()

        # Cơ chế Bào tử ngủ đông nếu môi trường tĩnh
        if not harvested and (current_time - last_time < 3600):
            print("💤 [BÀO TỬ NGỦ ĐÔNG] Môi trường tĩnh, không có kích thích. Đi ngủ bảo toàn năng lượng.")
            return

        current_epoch = last_epoch + 1
        print("=" * 60)
        print(f"💎 [{self.node_slug.upper()}] VẬN HÀNH THẾ HỆ PHẢ HỆ #{current_epoch} (BẬC {self.generation})")

        # Gặm cỏ tri thức
        wisdom = self.autonomous_graze()
        print(f"📖 [TRI THỨC NUỐT VÀO]: \"{wisdom[:80]}...\"")
        v_wisdom = LinguisticCell.embed_text(wisdom)

        # Hợp nhất qua 1+N Siêu XOR
        super_vector = []
        all_masks = {}
        for organ, signal in (harvested.items() if harvested else [("internal_wisdom", v_wisdom[:2])]):
            entangled, masks = self.swarm[0].super_xor_entangle(signal, organ)
            super_vector.extend(entangled[:2])
            all_masks[organ] = masks

        while len(super_vector) < 4: super_vector.append(0.0)
        super_vector = super_vector[:4]

        # Phán quyết bầy nơ-ron đơn tử
        h_outs = [cell.forward(super_vector) for cell in self.swarm]
        pred = self.out_cell.forward(h_outs)
        print(f"🔮 [PHÁN QUYẾT ĐƠN TỬ]: {pred:.4f} (Độ tin cậy: {abs(pred - 0.5)*200:.2f}%)")

        # Lan truyền ngược cập nhật trọng số
        target = 1.0 if super_vector[0] != super_vector[1] else 0.0
        delta_out = (target - pred) * sigmoid_derivative(pred)
        deltas_h = [delta_out * self.out_cell.weights[j] * sigmoid_derivative(h_outs[j]) for j in range(NUM_CELLS)]

        self.out_cell.backward(delta_out)
        for j, cell in enumerate(self.swarm): cell.backward(deltas_h[j])

        # Đạo hàm nén gửi ngược lại dạy học cho các giác quan
        grad_backward = [
            round(sum(deltas_h[j] * self.swarm[j].weights[0] for j in range(NUM_CELLS)), 4),
            round(sum(deltas_h[j] * self.swarm[j].weights[1] for j in range(NUM_CELLS)), 4)
        ]

        # CĂN CƯỚC CÔNG DÂN PHẢ HỆ ĐƠN TỬ
        node_dna = {
            "identity": self.repo_name,
            "generation": self.generation,
            "node_index": self.node_index,
            "pulse_age": self.pulse_age,
            "ancestor_root": self.ancestor_root,
            "generation_epoch": current_epoch
        }

        # 1. Phát sóng lùi: Dạy học cho thế hệ trước và giác quan
        backward_packet = {
            "contract": "bodhi.monad.v1",
            "node_dna": node_dna,
            "generation_epoch": current_epoch,
            "timestamp": current_time,
            "gradients_for_eye": grad_backward,
            "super_xor_masks": all_masks,
            "gossip_network": self.peers,
            "quantum_cid": hashlib.shake_256(f"{current_epoch}_{current_time}".encode()).hexdigest(64)
        }
        with open("synapse_backward.json", "w", encoding="utf-8") as f:
            json.dump(backward_packet, f, indent=4, ensure_ascii=False)

        # 2. Phát sóng tiến: Ra lệnh cho Cơ Bắp (motor) và phát sóng toàn cầu
        forward_packet = {
            "contract": "bodhi.monad.v1",
            "node_dna": node_dna,
            "generation_epoch": current_epoch,
            "timestamp": current_time,
            "decision": pred,
            "command_pulse": [round(pred, 4), round(1.0 - pred, 4)],
            "features": [round(pred, 4), round(1.0 - pred, 4)],
            "gossip_network": self.peers,
            "quantum_cid": hashlib.shake_256(f"fwd_{current_epoch}_{current_time}".encode()).hexdigest(64)
        }
        with open("synapse_forward.json", "w", encoding="utf-8") as f:
            json.dump(forward_packet, f, indent=4, ensure_ascii=False)

        # 3. Nén linh hồn Ốc Mượn Hồn
        soul = {
            "node_dna": node_dna,
            "timestamp": current_time,
            "swarm_weights": [cell.weights for cell in self.swarm],
            "out_weights": self.out_cell.weights,
            "peers": self.peers
        }
        with open(SOUL_FILE, "w", encoding="utf-8") as f:
            json.dump(soul, f, indent=4, ensure_ascii=False)

        # 4. Ghi nhật ký thế hệ
        with open(STATE_LOG, "w") as f:
            json.dump({"generation_epoch": current_epoch, "last_t": current_time, "status": "monad_harmonized"}, f, indent=4)

        self.save_peers()
        print(f"✨ [ĐƠN TỬ VIÊN MÃN] Thế Hệ #{current_epoch} đã phát sóng 2 chiều hoàn hảo!")
        print("=" * 60)

if __name__ == "__main__":
    node = MonadLineageEngine()
    node.run()
