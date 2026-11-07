"""Conservative lumped-capacity P1 FEM on a conforming annular/rectangular mesh.

Per unit pipe length; positive heat q leaves the gas. No empirical calibration.
The surface and deep boundary are isothermal; vertical sides are insulated.
The reduced model is a Galerkin projection, not an empirical response fit.
"""
from dataclasses import dataclass
import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import spsolve, splu
from scipy.linalg import eigh


@dataclass
class Thermal:
    K: object
    C: np.ndarray
    b: np.ndarray
    g: float
    xy: np.ndarray
    triangles: np.ndarray
    free: np.ndarray

    @property
    def steady(self):
        return spsolve(self.K, self.b)

    @property
    def conductance(self):
        return self.g - self.b @ self.steady

    def step_response(self, times, dt, amplitude=70.):
        x = np.zeros(len(self.C)); t = 0.; rows = []
        fact = {}; energy = 0.; boundary = 0.
        for target in times:
            while t < target - 1e-8:
                h = min(dt, target-t)
                key = round(h, 7)
                if key not in fact:
                    fact[key] = splu((self.K + diags(self.C/h)).tocsc())
                new = fact[key].solve(self.C/h*x + self.b*amplitude)
                q = self.g*amplitude-self.b@new
                loss = (np.asarray(self.K.sum(axis=0)).ravel()-self.b)@new
                boundary += h*(q-loss)
                energy = self.C@new
                x=new; t += h
            rows.append((target, self.g*amplitude-self.b@x, energy-boundary))
        return np.asarray(rows)

    def reduce(self, count=28):
        # Include the constant test function for an exact global energy balance
        # in the reduced subspace, and DC to preserve steady conductance.
        vectors = [np.ones(len(self.C)), self.steady]
        for s in np.logspace(-9, 2, count):
            vectors.append(spsolve(self.K + diags(s*self.C), self.b))
        A=np.column_stack(vectors)*np.sqrt(self.C)[:,None]
        # Unit-normalization prevents slow modes dominating rank selection.
        A /= np.linalg.norm(A,axis=0)
        u, singular, _ = np.linalg.svd(A,full_matrices=False)
        V=u[:,singular>singular[0]*1e-11]/np.sqrt(self.C)[:,None]
        Kr=V.T@(self.K@V); Kr=(Kr+Kr.T)/2
        lam,Q=eigh(Kr)
        if np.min(lam)<=0: raise ValueError('Non-passive thermal projection')
        V=V@Q
        return Reduced(lam,V.T@self.b,self.g,self.C@V,V)


@dataclass
class Reduced:
    lam: np.ndarray
    b: np.ndarray
    g: float
    storage: np.ndarray
    V: np.ndarray

    @property
    def conductance(self): return self.g-np.sum(self.b*self.b/self.lam)

    def steady(self, temperature):
        return self.b[:,None]/self.lam[:,None]*np.atleast_1d(temperature)[None,:]

    def affine(self,x,dt):
        decay=1/(1+dt*self.lam)
        coefficient=self.g-dt*np.sum(self.b*self.b*decay)
        offset=self.b@(decay[:,None]*x)
        return coefficient,offset

    def step(self,x,T,dt):
        return (x+dt*self.b[:,None]*np.atleast_1d(T)[None,:])/(1+dt*self.lam[:,None])

    def energy(self,x): return self.storage@x

    def environmental_loss(self,x):
        return (self.storage*self.lam-self.b)@x


def mesh_model(*, radii=(.125,.137), conductivity=(45.,1.5),
               capacity=(3.5e6,2e6), burial=1.5, width=48.,depth=60.,
               film=300., angular=96, layer_cells=3, soil_cells=45,
               annulus_outer=None,inner_dirichlet=False):
    """Full cross-section, material interfaces are conforming polygonal rings.

    width is half-width. Angles include rectangular corners exactly. Variable
    radius outer rings meet the rectangular boundary without cutting cells.
    """
    ri=radii[0]; ro=radii[-1]
    if len(conductivity)!=len(radii) or len(capacity)!=len(radii):
        raise ValueError('One solid material per annulus and a final soil material')
    corners=np.mod(np.arctan2([burial,burial,burial-depth,burial-depth],
                              [width,-width,-width,width]),2*np.pi)
    angles=np.unique(np.r_[np.linspace(0,2*np.pi,angular,endpoint=False),corners])
    ca,sa=np.cos(angles),np.sin(angles); na=len(angles)
    with np.errstate(divide='ignore'):
        vertical=np.where(np.abs(sa)<1e-14,np.inf,np.where(sa>0,burial/sa,(burial-depth)/sa))
        reach=np.minimum(width/np.abs(ca),vertical)
    if annulus_outer is not None:reach=np.full(na,annulus_outer)
    rings=[]; mats=[]
    for j in range(len(radii)-1):
        rr=np.linspace(radii[j],radii[j+1],layer_cells+1)
        for r in rr[:-1]: rings.append(np.full(na,r)); mats.append(j)
    # Geometric nearfield grading, then stretch to the rectangular boundary.
    nr=max(10,int(soil_cells*.68)); far=soil_cells-nr
    rr=np.geomspace(ro,.72*(burial if annulus_outer is None else annulus_outer),nr+1)
    for r in rr[:-1]: rings.append(np.full(na,r)); mats.append(len(radii)-1)
    for f in np.linspace(0,1,far+1):
        rings.append(rr[-1]*(reach/rr[-1])**f); mats.append(len(radii)-1)
    xy=np.concatenate([np.column_stack([r*ca,r*sa]) for r in rings])
    triangles=[]; tri_mat=[]
    for j in range(len(rings)-1):
        for a in range(na):
            n=(a+1)%na; x=j*na+a; y=j*na+n; z=(j+1)*na+a; w=(j+1)*na+n
            triangles.extend([(x,z,w),(x,w,y)]); tri_mat.extend([mats[j]]*2)
    triangles=np.asarray(triangles); tri_mat=np.asarray(tri_mat)
    verts=xy[triangles]; d1=verts[:,1]-verts[:,0]; d2=verts[:,2]-verts[:,0]
    area=np.abs(d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0])/2
    # Gradients of P1 basis functions; orientation signs cancel in products.
    bgrad=np.stack([verts[:,1,1]-verts[:,2,1],verts[:,2,1]-verts[:,0,1],verts[:,0,1]-verts[:,1,1]],axis=1)
    cgrad=np.stack([verts[:,2,0]-verts[:,1,0],verts[:,0,0]-verts[:,2,0],verts[:,1,0]-verts[:,0,0]],axis=1)
    kel=(bgrad[:,:,None]*bgrad[:,None,:]+cgrad[:,:,None]*cgrad[:,None,:])
    kel *= np.asarray(conductivity)[tri_mat,None,None]/(4*area[:,None,None])
    I=np.broadcast_to(triangles[:,:,None],kel.shape).ravel(); J=np.broadcast_to(triangles[:,None,:],kel.shape).ravel()
    cap=np.zeros(len(xy)); np.add.at(cap,triangles.ravel(),np.repeat(np.asarray(capacity)[tri_mat]*area/3,3))
    bvec=np.zeros(len(xy)); extraI=[]; extraJ=[]; extraV=[]
    for a in range(na):
        n=(a+1)%na; length=np.linalg.norm(xy[a]-xy[n]); h=film*length
        bvec[[a,n]]+=h/2
        extraI.extend([a,a,n,n]);extraJ.extend([a,n,a,n]);extraV.extend([h/3,h/6,h/6,h/3])
    K=coo_matrix((np.r_[kel.ravel(),extraV],(np.r_[I,extraI],np.r_[J,extraJ])),shape=(len(xy),len(xy))).tocsr()
    fixed=np.isclose(xy[:,1],burial,atol=1e-9)|np.isclose(xy[:,1],burial-depth,atol=1e-9)
    if annulus_outer is not None:fixed=np.arange(len(xy))>=(len(rings)-1)*na
    if inner_dirichlet:fixed[:na]=True
    free=~fixed
    return Thermal(K[free][:,free],cap[free],bvec[free],bvec.sum(),xy,triangles,free)


def analytical_conductance(radii,conductivity,burial,film):
    R=1/(film*2*np.pi*radii[0])
    for j in range(len(radii)-1): R+=np.log(radii[j+1]/radii[j])/(2*np.pi*conductivity[j])
    R+=np.arccosh(burial/radii[-1])/(2*np.pi*conductivity[-1])
    return 1/R

