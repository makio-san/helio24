"""Small CNN for SHARP Br maps. Torch only: never import sklearn or xgboost into the same process."""
import numpy as np


def build_net(dropout):
    import torch
    from torch import nn

    class MapNet(nn.Module):
        def __init__(self):
            super().__init__()
            layers, channels = [], 1
            for width in (16, 32, 64, 128):
                layers += [nn.Conv2d(channels, width, 3, padding=1), nn.BatchNorm2d(width), nn.ReLU(), nn.MaxPool2d(2)]
                channels = width
            self.features = nn.Sequential(*layers)
            self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(2*channels+3, 1))

        def forward(self, image, extra):
            maps = self.features(image)
            return self.head(torch.cat([maps.mean((2, 3)), maps.amax((2, 3)), extra], 1))[:, 0]
    return MapNet()


def _batch(images, extra, index, device):
    import torch
    image = torch.from_numpy(np.clip(images[index].astype(np.float32)/500, -6, 6))[:, None].to(device)
    return image, torch.from_numpy(extra[index]).to(device)


def train_cnn(images, extra, labels, settings, seed, device):
    import torch
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = build_net(settings['dropout']).to(device)
    optimiser = torch.optim.Adam(model.parameters(), lr=settings['learning_rate'], weight_decay=settings['weight_decay'])
    loss_fn = torch.nn.BCEWithLogitsLoss()
    target = torch.from_numpy(labels.astype(np.float32))
    last = float('nan')
    for _ in range(settings['epochs']):
        model.train()
        order, total = rng.permutation(len(labels)), 0.0
        for start in range(0, len(order), settings['batch']):
            index = np.sort(order[start:start+settings['batch']])
            image, scalars = _batch(images, extra, index, device)
            flip = torch.from_numpy(rng.random(len(index)) < 0.5).to(device)
            image = torch.where(flip[:, None, None, None], image.flip(3), image)
            sign = torch.from_numpy(np.where(rng.random(len(index)) < 0.5, -1.0, 1.0).astype(np.float32)).to(device)
            loss = loss_fn(model(image*sign[:, None, None, None], scalars), target[index].to(device))
            optimiser.zero_grad()
            loss.backward()
            optimiser.step()
            total += loss.item()*len(index)
        last = total/len(order)
    return model, last


def score_cnn(model, images, extra, index, device, batch=256):
    import torch
    model.eval()
    out = np.empty(len(index), dtype=np.float32)
    with torch.no_grad():
        for start in range(0, len(index), batch):
            part = index[start:start+batch]
            out[start:start+len(part)] = model(*_batch(images, extra, part, device)).cpu().numpy()
    return out


def pick_device():
    import torch
    return 'mps' if torch.backends.mps.is_available() else 'cpu'
